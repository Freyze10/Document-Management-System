"""
Fill the MSDS Word templates (DC / MB1 / MB2) through Word COM (pywin32),
then export to PDF (for the preview / download) or print.

Templates live in  <app resources>/print/template-msds/
    dc.docx   -> has the 5 hazard bullets in Section 3
    mb1.docx  -> single general-note paragraph in Section 3, plain Section 2
    mb2.docx  -> same as mb1 + ingredient breakdown table in Section 2
                 (Common Name | Color Index No. | CAS No.)

Template choice:
    msds_section_2 has rows                  -> mb2.docx
    else any of the 5 hazard fields filled   -> dc.docx
    else                                     -> mb1.docx

Every value in the templates is a plain-text token like [[TRADE_NAME]].
Tokens that don't exist in a template are simply skipped, so ONE token map
serves all templates.

SPEED  (why the first preview of a record used to be slow)
    1. Word is started in the background at app start            -> warm_up()
    2. One spare copy of every template is kept OPEN and idle;
       a preview uses it, then a fresh spare is opened afterwards -> _spares
    3. The first export after Word starts is slow (fonts, PDF engine);
       a spare is exported once at start-up to get that out of the way
    4. A record can be rendered BEFORE the user clicks Preview
       (call prefetch_async when a record is selected)            -> prefetch_async()
    5. Everything runs on ONE worker thread with priorities:
       a user click always jumps ahead of background work.
    Set TIMING = True to print where the time goes for each render.
"""
import hashlib
import itertools
import os
import queue
import shutil
import tempfile
import threading
import time
import uuid
from collections import OrderedDict
from concurrent.futures import Future

import pythoncom
import pywintypes
import win32com.client as win32

from utils import abs_path
from print import word_layout

TEMPLATE_DC = "print/template-msds/dc.docx"
TEMPLATE_MB1 = "print/template-msds/mb1.docx"
TEMPLATE_MB2 = "print/template-msds/mb2.docx"
ALL_TEMPLATES = (TEMPLATE_MB1, TEMPLATE_DC, TEMPLATE_MB2)

TIMING = True       # print "[msds timing] ..." for every render (set False when you are done measuring)

# Word constants (late-bound COM has no named constants)
WD_FORMAT_PDF = 17
WD_ALERTS_NONE = 0
WD_DO_NOT_SAVE = 0

# job priorities (lower number runs first)
PRIO_STOP = -1        # shutdown
PRIO_USER = 0         # the user clicked Preview / Print
PRIO_START = 1        # start Word
PRIO_SPARE = 4        # re-open a spare template after one was used
PRIO_PREFETCH = 5     # render a record before it is asked for
PRIO_WARM = 6         # start-up: pre-open spares + warm the PDF engine

S9_NAME_TOKEN = "[[S9_NAME]]"
S9_VALUE_TOKEN = "[[S9_VALUE]]"
S2_HEADER_TEXT = "Common Name"      # first header cell of the mb2 breakdown table

# token -> index in db_con.get_single_msds_data()
FIELD_MAP = {
    "TRADE_NAME": 2,
    "MANUFACTURED_BY": 6,
    "TEL": 7,
    "FAX": 8,                 # DC: "Facsimile"   |  MB: "Mobile/Viber No"
    "EMAIL": 9,
    "COMPOSITION": 10,
    "HAZARD_PRELIM": 11,      # DC only
    "HAZARD_ROUTE": 12,       # DC only
    "HAZARD_SYMPTOMS": 13,    # DC only
    "HAZARD_RESTRICTIVE": 14, # DC only
    "HAZARD_EYES": 15,        # DC only
    "HAZARD_NOTE": 16,        # both
    "FA_INHALATION": 17,
    "FA_EYES": 18,
    "FA_SKIN": 19,
    "FA_INGESTION": 20,
    "FIRE_FIGHTING": 21,
    "ACCIDENTAL_RELEASE": 22,
    "HANDLING": 23,           # DC only
    "STORAGE": 24,            # both
    "EXPOSURE_CONTROL": 25,
    "RESPIRATORY": 26,
    "HAND": 27,
    "EYE": 28,
    "SKIN": 29,
    "STABILITY": 30,
    "AVOID_CONDITIONS": 31,
    "AVOID_MATERIALS": 32,
    "DECOMPOSITION": 33,
    "TOXICOLOGICAL": 34,
    "ECOLOGICAL": 35,
    "DISPOSAL": 36,
    "TRANSPORT": 37,
    "REGULATORY": 38,
    "SHELF_LIFE": 39,
    "OTHER": 40,
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _s(value):
    """None -> '', everything else -> stripped str."""
    return "" if value is None else str(value).strip()


def is_dc(row):
    """Any of the 5 hazard fields filled in => DC template."""
    return any(_s(row[i]) for i in range(11, 16))


def _section2_clean(section2_rows):
    """DB rows (id, msds_id, row_order, common_name, color_index_no, cas_no)
    -> [(name, color_index, cas)] without completely empty rows."""
    out = []
    for r in (section2_rows or []):
        item = (_s(r[3]), _s(r[4]), _s(r[5]))
        if any(item):
            out.append(item)
    return out


def _pick_template(row, section2_rows):
    if _section2_clean(section2_rows):
        return TEMPLATE_MB2
    if is_dc(row):
        return TEMPLATE_DC
    return TEMPLATE_MB1


def _build_tokens(row):
    return {f"[[{name}]]": _s(row[idx]) for name, idx in FIELD_MAP.items()}


class _Timer:
    """Collects 'step: seconds' for one render and prints one line at the end."""

    def __init__(self, label):
        self.label = label
        self.t0 = self.last = time.perf_counter()
        self.laps = []

    def lap(self, name):
        now = time.perf_counter()
        self.laps.append((name, now - self.last))
        self.last = now

    def report(self, note=""):
        if not TIMING:
            return
        steps = " | ".join(f"{n} {d:.2f}s" for n, d in self.laps)
        total = time.perf_counter() - self.t0
        print(f"[msds timing] {self.label}: {steps} | TOTAL {total:.2f}s {note}".rstrip(), flush=True)


def _fill_token(doc, token, value):
    """Replace the first occurrence of `token` with `value`.

    Uses Range.Text instead of Find.Replace because Replace.Text is limited
    to 255 characters and several of the values are longer than that.
    The replacement inherits the formatting of the token, so format the
    token in the template exactly how the output should look.
    """
    rng = doc.Content
    find = rng.Find
    find.ClearFormatting()
    find.Text = token
    find.Forward = True
    find.Wrap = 0            # wdFindStop
    find.MatchCase = True
    find.MatchWildcards = False
    if find.Execute():
        # keep multi-line values inside the same paragraph / cell
        rng.Text = value.replace("\r\n", "\v").replace("\n", "\v").replace("\r", "\v")
        return True
    return False


def _fill_section2(doc, section2_rows):
    """mb2 only: Section 2 breakdown table (header + sample rows in the template).
    Keep the header and the first data row (as the formatting row), drop the
    other sample rows, then add one row per DB record.

    In the CAS column use ';' to put several numbers in one cell,
    each one is printed on its own line."""
    table = None
    for t in doc.Tables:
        if S2_HEADER_TEXT in t.Range.Text:
            table = t
            break
    if table is None:
        return

    rows = _section2_clean(section2_rows)
    if not rows:
        return

    for i in range(table.Rows.Count, 2, -1):    # keep header (1) + first data row (2)
        table.Rows(i).Delete()

    for _ in range(len(rows) - 1):
        table.Rows.Add()                        # copies formatting of the last row

    for i, (name, color_index, cas) in enumerate(rows, start=2):   # Word is 1-based
        cas = "\r".join(p.strip() for p in cas.split(";") if p.strip())
        table.Cell(i, 1).Range.Text = name
        table.Cell(i, 2).Range.Text = color_index
        table.Cell(i, 3).Range.Text = cas


def _fill_section9(doc, section9_rows):
    """Section 9 is a 3-column table (name | ':' | value) with ONE template row.
    Add a row per property saved in the DB."""
    table = None
    for t in doc.Tables:
        if S9_NAME_TOKEN in t.Range.Text:
            table = t
            break
    if table is None:
        return

    rows = [(_s(r[3]), _s(r[4])) for r in (section9_rows or [])]
    if not rows:
        table.Delete()
        return

    for _ in range(len(rows) - 1):
        table.Rows.Add()             # copies formatting of the last row

    for i, (name, value) in enumerate(rows, start=1):   # Word is 1-based
        table.Cell(i, 1).Range.Text = name
        table.Cell(i, 2).Range.Text = ":"
        table.Cell(i, 3).Range.Text = value


def _section9_starts_page2(doc):
    """MB: heading 9 should start page 2.
    If it lands on page 1, force a page break before it.
    If section 8 already runs onto page 2, leave the normal flow alone."""
    rng = doc.Content
    find = rng.Find
    find.ClearFormatting()
    find.Text = "Physical & Chemical Properties"   # must match the heading text
    find.Forward = True
    find.Wrap = 0                                   # wdFindStop
    find.MatchCase = True
    find.MatchWildcards = False
    if not find.Execute():
        return
    para = rng.Paragraphs(1)
    para.Format.PageBreakBefore = False
    doc.Repaginate()
    if rng.Information(3) == 1:                     # 3 = wdActiveEndPageNumber
        para.Format.PageBreakBefore = True


# --------------------------------------------------------------------------
# ONE worker thread that owns Word. Priority queue: user clicks first.
#
# COM objects must be used from the thread that created them, so every Word
# call goes through this thread. Callers get a Future back and never block
# the GUI thread. Background jobs (prefetch, spares, warm-up) have a higher
# priority NUMBER, so a user click waits at most for the job already running.
# --------------------------------------------------------------------------
class _Worker:
    def __init__(self):
        self._q = queue.PriorityQueue()
        self._seq = itertools.count()
        self._thread = threading.Thread(target=self._run, name="word-com", daemon=True)
        self._thread.start()

    def submit(self, fn, *args, priority=PRIO_USER):
        fut = Future()
        self._q.put((priority, next(self._seq), fut, fn, args))
        return fut

    def stop(self):
        self._q.put((PRIO_STOP, next(self._seq), None, None, ()))

    def _run(self):
        pythoncom.CoInitialize()
        try:
            while True:
                _prio, _seq, fut, fn, args = self._q.get()
                if fn is None:                      # stop sentinel
                    break
                if not fut.set_running_or_notify_cancel():
                    continue
                try:
                    fut.set_result(fn(*args))
                except BaseException as e:          # noqa: BLE001 - handed to the caller
                    fut.set_exception(e)
        finally:
            pythoncom.CoUninitialize()


_worker = _Worker()
_lock = threading.Lock()           # guards _pending / _spare_pending (touched by GUI + worker thread)
_word = None                       # worker thread only
_cache = OrderedDict()             # worker thread writes; key lookups from the GUI thread are safe
_CACHE_SIZE = 20
_pending = set()                   # cache keys queued for prefetch
_spares = {}                       # template path -> _Spare (worker thread only)
_spare_pending = set()             # templates with a spare job queued
_engine_warm = False


class _Spare:
    """A template copy that is already open in Word and waiting to be filled."""

    def __init__(self, doc, tmpdir, mtime):
        self.doc, self.tmpdir, self.mtime = doc, tmpdir, mtime


def _get_word():
    """(worker thread) Return the shared Word, starting it if needed."""
    global _word
    if _word is not None:
        try:
            _word.Version            # ping: raises if the user killed Word
            return _word
        except Exception:
            _forget_spares()
            _word = None
    # DispatchEx = our own instance; never grabs a Word window the user has open
    _word = win32.DispatchEx("Word.Application")
    _word.Visible = False
    _word.DisplayAlerts = WD_ALERTS_NONE
    _word.ScreenUpdating = False
    return _word


def _forget_spares():
    """Word died / was restarted: the open spare documents are gone with it."""
    global _engine_warm
    for sp in _spares.values():
        shutil.rmtree(sp.tmpdir, ignore_errors=True)
    _spares.clear()
    _engine_warm = False


def _reset_word():
    global _word
    try:
        if _word is not None:
            _word.Quit(SaveChanges=WD_DO_NOT_SAVE)
    except Exception:
        pass
    _word = None
    _forget_spares()


def _discard_spare(sp):
    try:
        sp.doc.Close(SaveChanges=WD_DO_NOT_SAVE)
    except Exception:
        pass
    shutil.rmtree(sp.tmpdir, ignore_errors=True)


# --------------------------------------------------------------------------
# spare templates
# --------------------------------------------------------------------------
def _copy_template(template):
    """-> (tmpdir, path of a private copy). Unique file name so Word never
    mistakes two open copies for the same document."""
    src = abs_path.resource(template)
    tmpdir = tempfile.mkdtemp(prefix="msds_")
    dst = os.path.join(tmpdir, f"{uuid.uuid4().hex[:8]}_{os.path.basename(src)}")
    shutil.copy(src, dst)
    return tmpdir, os.path.abspath(dst)


def _make_spare(template, warm_engine=False):
    """(worker thread) Open one idle copy of `template`."""
    global _engine_warm
    tmpdir = None
    try:
        if template in _spares:
            return
        word = _get_word()
        tmpdir, dst = _copy_template(template)
        mtime = os.path.getmtime(abs_path.resource(template))
        doc = word.Documents.Open(dst, ReadOnly=False, AddToRecentFiles=False, Visible=False)
        if warm_engine and not _engine_warm:
            # the first export after Word starts is slow (fonts, PDF engine): do it now, once
            t = time.perf_counter()
            doc.ExportAsFixedFormat(OutputFileName=os.path.join(tmpdir, "warm.pdf"),
                                    ExportFormat=WD_FORMAT_PDF)
            _engine_warm = True
            if TIMING:
                print(f"[msds timing] PDF engine warm-up: {time.perf_counter() - t:.2f}s", flush=True)
        _spares[template] = _Spare(doc, tmpdir, mtime)
        tmpdir = None                      # now owned by the spare
    except Exception as e:                 # a spare is optional: never break anything for it
        if TIMING:
            print(f"[msds timing] spare for {os.path.basename(template)} failed: {e}", flush=True)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
        with _lock:
            _spare_pending.discard(template)


def _schedule_spare(template, warm_engine=False, priority=PRIO_SPARE):
    with _lock:
        if template in _spares or template in _spare_pending:
            return
        _spare_pending.add(template)
    _worker.submit(_make_spare, template, warm_engine, priority=priority)


def _acquire_template(word, template):
    """-> (doc, tmpdir, from_spare). Uses the idle spare if there is a valid one."""
    spare = _spares.pop(template, None)
    if spare is not None:
        try:
            if spare.mtime == os.path.getmtime(abs_path.resource(template)):   # template not edited meanwhile
                spare.doc.Name                                                  # ping: raises if closed
                return spare.doc, spare.tmpdir, True
        except Exception:
            pass
        _discard_spare(spare)

    tmpdir, dst = _copy_template(template)
    try:
        doc = word.Documents.Open(dst, ReadOnly=False, AddToRecentFiles=False, Visible=False)
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    return doc, tmpdir, False


def _open_filled_doc(word, row, section9_rows, section2_rows, timer):
    """-> (doc, tmpdir). Caller closes the doc and deletes tmpdir."""
    template = _pick_template(row, section2_rows)
    doc, tmpdir, from_spare = _acquire_template(word, template)
    timer.label = f"{os.path.basename(template)}{' (spare)' if from_spare else ' (opened now)'}"
    timer.lap("open")
    try:
        # Tables first (their tokens / sample rows live inside tables), then everything else
        if template == TEMPLATE_MB2:
            _fill_section2(doc, section2_rows)
        _fill_section9(doc, section9_rows)
        for token, value in _build_tokens(row).items():
            _fill_token(doc, token, value)
        timer.lap("fill")

        word_layout.keep_sections_together(doc)

        # Section 8's length is only known now, so decide the page break last
        if template != TEMPLATE_DC:      # MB1 / MB2
            _section9_starts_page2(doc)
        timer.lap("layout")
    except Exception:
        try:
            doc.Close(SaveChanges=WD_DO_NOT_SAVE)
        except Exception:
            pass
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise

    _schedule_spare(template)            # open a fresh idle copy for the next record
    return doc, tmpdir


# --------------------------------------------------------------------------
# jobs (all run on the worker thread)
# --------------------------------------------------------------------------
def _cache_key(row, section9_rows, section2_rows):
    raw = repr((tuple(row),
                tuple(tuple(r) for r in (section9_rows or [])),
                tuple(tuple(r) for r in (section2_rows or []))))
    return hashlib.md5(raw.encode("utf8")).hexdigest()


def _with_retry(fn, *args):
    """If Word died (RPC error) restart it once and try again."""
    try:
        return fn(*args)
    except pywintypes.com_error:
        _reset_word()
        return fn(*args)


def _render_job(row, section9_rows, section2_rows, source="preview"):
    key = _cache_key(row, section9_rows, section2_rows)
    if key in _cache:
        _cache.move_to_end(key)
        if TIMING:
            print(f"[msds timing] {source}: served from cache (0.00s)", flush=True)
        return _cache[key]

    timer = _Timer(source)

    def run():
        word = _get_word()
        timer.lap("word")
        doc, tmpdir = _open_filled_doc(word, row, section9_rows, section2_rows, timer)
        try:
            pdf_path = os.path.join(tmpdir, "msds.pdf")
            doc.ExportAsFixedFormat(OutputFileName=os.path.abspath(pdf_path),
                                    ExportFormat=WD_FORMAT_PDF)
            timer.lap("export")
            with open(pdf_path, "rb") as f:
                data = f.read()
            timer.lap("read")
            return data
        finally:
            try:
                doc.Close(SaveChanges=WD_DO_NOT_SAVE)
            except Exception:
                pass
            shutil.rmtree(tmpdir, ignore_errors=True)

    data = _with_retry(run)
    _cache[key] = data
    if len(_cache) > _CACHE_SIZE:
        _cache.popitem(last=False)
    timer.report(f"[{source}]")
    return data


def _prefetch_job(key, row, section9_rows, section2_rows):
    try:
        _render_job(row, section9_rows, section2_rows, source="prefetch")
    except Exception:
        pass                                   # background work must never raise into the app
    finally:
        with _lock:
            _pending.discard(key)


def _print_job(row, section9_rows, section2_rows, printer_name, copies):
    timer = _Timer("print")

    def run():
        word = _get_word()
        timer.lap("word")
        doc, tmpdir = _open_filled_doc(word, row, section9_rows, section2_rows, timer)
        try:
            if printer_name:
                word.ActivePrinter = printer_name
            # Background=False: wait until the job is in the spooler
            doc.PrintOut(Background=False, Copies=max(1, int(copies)))
            timer.lap("print")
        finally:
            try:
                doc.Close(SaveChanges=WD_DO_NOT_SAVE)
            except Exception:
                pass
            shutil.rmtree(tmpdir, ignore_errors=True)

    _with_retry(run)
    timer.report("[print]")


def _shutdown_job():
    for sp in list(_spares.values()):
        _discard_spare(sp)
    _spares.clear()
    _reset_word()


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------
def warm_up():
    """Call once at app start (safe to repeat).
    Starts Word, then in the background pre-opens one idle copy of every
    template and warms up the PDF engine."""
    fut = _worker.submit(_get_word, priority=PRIO_START)
    for i, template in enumerate(ALL_TEMPLATES):
        _schedule_spare(template, warm_engine=(i == 0), priority=PRIO_WARM)
    return fut


def prefetch_async(row, section9_rows, section2_rows=None):
    """Render this record's PDF in the background so Preview opens instantly.
    Call it when a record is SELECTED in the list. Does nothing if the record
    is already cached or already queued. Returns a Future or None."""
    key = _cache_key(row, section9_rows, section2_rows)
    with _lock:
        if key in _cache or key in _pending:
            return None
        _pending.add(key)
    return _worker.submit(_prefetch_job, key, row, section9_rows, section2_rows,
                          priority=PRIO_PREFETCH)


def render_pdf_async(row, section9_rows, section2_rows=None):
    """-> Future[bytes]  (PDF of the filled DC/MB1/MB2 template)"""
    return _worker.submit(_render_job, row, section9_rows, section2_rows, "preview",
                          priority=PRIO_USER)


def print_msds_async(row, section9_rows, section2_rows=None, printer_name=None, copies=1):
    """-> Future[None]  (resolves when the job has reached the spooler)"""
    return _worker.submit(_print_job, row, section9_rows, section2_rows, printer_name, copies,
                          priority=PRIO_USER)


def render_pdf_bytes(row, section9_rows, section2_rows=None):
    """Blocking version, if you ever need it outside the GUI thread."""
    return render_pdf_async(row, section9_rows, section2_rows).result()


def shutdown():
    """Quit the hidden Word. Connect to QApplication.aboutToQuit, otherwise a
    WINWORD.exe is left running in the background."""
    try:
        _worker.submit(_shutdown_job, priority=PRIO_STOP).result(timeout=10)
    except Exception:
        pass
    _worker.stop()