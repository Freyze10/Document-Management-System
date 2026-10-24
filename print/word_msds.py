"""
Fill the MSDS Word templates (DC / MB) through Word COM (pywin32),
then export to PDF (for the preview / download) or print.

Templates live in  <app resources>/templates/
    msds_dc.docx   -> has the 5 hazard bullets in Section 3 (old "else" branch)
    msds_mb.docx   -> single general-note paragraph in Section 3 (old "all empty" branch)

Every value in the templates is a plain-text token like [[TRADE_NAME]].
Tokens that don't exist in a template are simply skipped, so ONE token map
serves both templates.
"""
import hashlib
import os
import shutil
import tempfile
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import pythoncom
import pywintypes
import win32com.client as win32

from utils import abs_path

TEMPLATE_DC = "print/template-msds/dc.docx"
TEMPLATE_MB = "print/template-msds/mb1.docx"

# Word constants (late-bound COM has no named constants)
WD_FORMAT_PDF = 17
WD_ALERTS_NONE = 0
WD_DO_NOT_SAVE = 0

S9_NAME_TOKEN = "[[S9_NAME]]"
S9_VALUE_TOKEN = "[[S9_VALUE]]"

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
    """Same rule as before: any of the 5 hazard fields filled in => DC template."""
    return any(_s(row[i]) for i in range(11, 16))


def _build_tokens(row):
    return {f"[[{name}]]": _s(row[idx]) for name, idx in FIELD_MAP.items()}


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


def _open_filled_doc(word, row, section9_rows, workdir):
    template = TEMPLATE_DC if is_dc(row) else TEMPLATE_MB
    src = abs_path.resource(template)
    tmp = os.path.join(workdir, os.path.basename(src))
    shutil.copy(src, tmp)            # never touch the real template

    doc = word.Documents.Open(os.path.abspath(tmp), ReadOnly=False,
                              AddToRecentFiles=False, Visible=False)

    # Section 9 first (its tokens live inside a table), then everything else
    _fill_section9(doc, section9_rows)
    for token, value in _build_tokens(row).items():
        _fill_token(doc, token, value)
    return doc


# --------------------------------------------------------------------------
# One persistent, invisible Word on ONE dedicated thread.
#
# COM objects must be used from the thread that created them, so every Word
# call goes through this single-thread executor. Callers get a Future back and
# never block the GUI thread.
# --------------------------------------------------------------------------
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="word-com",
                               initializer=pythoncom.CoInitialize)
_word = None
_cache = OrderedDict()      # only touched from the worker thread
_CACHE_SIZE = 10


def _get_word():
    """(worker thread) Return the shared Word, starting it if needed."""
    global _word
    if _word is not None:
        try:
            _word.Version            # ping: raises if the user killed Word
            return _word
        except Exception:
            _word = None
    # DispatchEx = our own instance; never grabs a Word window the user has open
    _word = win32.DispatchEx("Word.Application")
    _word.Visible = False
    _word.DisplayAlerts = WD_ALERTS_NONE
    _word.ScreenUpdating = False
    return _word


def _reset_word():
    global _word
    try:
        if _word is not None:
            _word.Quit(SaveChanges=WD_DO_NOT_SAVE)
    except Exception:
        pass
    _word = None


def _cache_key(row, section9_rows):
    raw = repr((tuple(row), tuple(tuple(r) for r in (section9_rows or []))))
    return hashlib.md5(raw.encode("utf8")).hexdigest()


def _with_retry(fn, *args):
    """If Word died (RPC error) restart it once and try again."""
    try:
        return fn(*args)
    except pywintypes.com_error:
        _reset_word()
        return fn(*args)


def _render_job(row, section9_rows):
    key = _cache_key(row, section9_rows)
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]

    def run():
        word = _get_word()
        workdir = tempfile.mkdtemp(prefix="msds_")
        try:
            doc = _open_filled_doc(word, row, section9_rows, workdir)
            try:
                pdf_path = os.path.join(workdir, "msds.pdf")
                doc.ExportAsFixedFormat(OutputFileName=os.path.abspath(pdf_path),
                                        ExportFormat=WD_FORMAT_PDF)
            finally:
                doc.Close(SaveChanges=WD_DO_NOT_SAVE)
            with open(pdf_path, "rb") as f:
                return f.read()
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    data = _with_retry(run)
    _cache[key] = data
    if len(_cache) > _CACHE_SIZE:
        _cache.popitem(last=False)
    return data


def _print_job(row, section9_rows, printer_name, copies):
    def run():
        word = _get_word()
        workdir = tempfile.mkdtemp(prefix="msds_")
        try:
            doc = _open_filled_doc(word, row, section9_rows, workdir)
            try:
                if printer_name:
                    word.ActivePrinter = printer_name
                # Background=False: wait until the job is in the spooler
                doc.PrintOut(Background=False, Copies=max(1, int(copies)))
            finally:
                doc.Close(SaveChanges=WD_DO_NOT_SAVE)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    _with_retry(run)


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------
def warm_up():
    """Start Word in the background. Call once at app start (safe to repeat)."""
    return _executor.submit(_get_word)


def render_pdf_async(row, section9_rows):
    """-> Future[bytes]  (PDF of the filled DC/MB template)"""
    return _executor.submit(_render_job, row, section9_rows)


def print_msds_async(row, section9_rows, printer_name=None, copies=1):
    """-> Future[None]  (resolves when the job has reached the spooler)"""
    return _executor.submit(_print_job, row, section9_rows, printer_name, copies)


def render_pdf_bytes(row, section9_rows):
    """Blocking version, if you ever need it outside the GUI thread."""
    return render_pdf_async(row, section9_rows).result()


def shutdown():
    """Quit the hidden Word. Connect to QApplication.aboutToQuit, otherwise a
    WINWORD.exe is left running in the background."""
    try:
        _executor.submit(_reset_word).result(timeout=10)
    except Exception:
        pass
    _executor.shutdown(wait=False)