"""
word_layout.py  -  page-flow rules for the filled MSDS Word document (print/).

Rule 1  A numbered section (1) ... 17) ) is kept in ONE piece together with its number:
        if it does not fit at the bottom of a page, the whole section, starting from its
        number, moves to the next page.  No more "6) Accidental Release" alone at the
        bottom with its text on the next page.

Rule 2  Sections in SPLITTABLE_SECTIONS may continue on the next page, because they hold a
        table that can be long:
            2) the ingredient breakdown table   (its header row repeats on the next page)
            9) the physical & chemical properties table
        Their number + first rows stay together, and a single row is never cut in half.

Call  keep_sections_together(doc)  AFTER every token / table has been filled
(the length of the text is only known then).
"""
import re

_SECTION_NO = re.compile(r"^\s*(\d+)\s*\)")

# Sections whose table may run over to the next page. Add a number here to
# let another section split; remove one to keep it in a single piece.
SPLITTABLE_SECTIONS = {2, 9}

BREAKDOWN_HEADER_TEXT = "Common Name"        # first header cell of the section 2 table

DEBUG = False        # True -> prints "section: first page - last page" for every section

WD_ACTIVE_END_PAGE = 3       # Information(): page number
WD_WITHIN_TABLE = 12         # Information(): is the range inside a table


def _is_blank(par):
    """Empty line, or the empty cells / end-of-row marks of a blank table row."""
    text = par.Range.Text or ""
    return not text.replace("\r", "").replace("\x07", "").replace("\v", "").replace("\xa0", "").strip()


def _section_starts(doc):
    """[(section_number, start_position), ...] in document order."""
    heads = []
    for p in doc.ListParagraphs:                       # numbered / bulleted paragraphs only
        rng = p.Range
        m = _SECTION_NO.match(rng.ListFormat.ListString or "")
        if m:                                          # "6)" yes, a bullet no
            heads.append((int(m.group(1)), rng.Start))

    if not heads:                                      # numbers typed by hand, not a Word list
        for p in doc.Paragraphs:
            rng = p.Range
            m = _SECTION_NO.match(rng.Text or "")
            if m:
                heads.append((int(m.group(1)), rng.Start))

    heads.sort(key=lambda h: h[1])
    return heads


def _keep_in_one_piece(sec):
    """Glue every paragraph / table row of the section to the next one, so Word
    moves the whole block when it does not fit.

    Blank lines and blank table rows at the END of the section are only filler:
    they are released from the chain so they never decide whether the section
    fits (a section whose text fits must not be pushed away by an empty row)."""
    fmt = sec.ParagraphFormat
    fmt.KeepTogether = True            # no paragraph is cut across two pages
    fmt.KeepWithNext = True            # heading -> text -> text ...

    paras = sec.Paragraphs
    i = paras.Count
    while i >= 1:                      # walk back from the end of the section
        p = paras(i)
        p.KeepWithNext = False         # trailing filler + the last real paragraph: not glued to what follows
        if not _is_blank(p):
            if p.Range.Information(WD_WITHIN_TABLE):
                p.Range.Rows(1).Range.ParagraphFormat.KeepWithNext = False   # the whole last real row
            break
        i -= 1


def _let_table_split(doc, sec):
    """Section with a (possibly long) table: it may continue on the next page,
    but its number + the first rows stay together."""
    fmt = sec.ParagraphFormat
    fmt.KeepWithNext = False
    fmt.KeepTogether = True

    first = sec.Tables(1)
    # number (+ any text above the table) stays with the table's first rows
    doc.Range(sec.Start, first.Range.Start).ParagraphFormat.KeepWithNext = True
    if first.Rows.Count > 1:
        first.Rows(1).Range.ParagraphFormat.KeepWithNext = True     # row 1 + row 2 together
    if BREAKDOWN_HEADER_TEXT in first.Rows(1).Range.Text:
        first.Rows(1).HeadingFormat = True                          # repeat header on next page


def page_report(doc):
    """[(section_no, first_page, last_page), ...]  - handy to see where sections land."""
    heads = _section_starts(doc)
    doc_end = doc.Content.End
    out = []
    for i, (num, start) in enumerate(heads):
        end = heads[i + 1][1] if i + 1 < len(heads) else doc_end
        last = max(start, end - 1)
        out.append((num,
                    doc.Range(start, start).Information(WD_ACTIVE_END_PAGE),
                    doc.Range(last, last).Information(WD_ACTIVE_END_PAGE)))
    return out


def keep_sections_together(doc):
    for t in doc.Tables:
        t.Rows.AllowBreakAcrossPages = False           # never cut ONE row across two pages

    heads = _section_starts(doc)
    doc_end = doc.Content.End
    for i, (num, start) in enumerate(heads):
        end = heads[i + 1][1] if i + 1 < len(heads) else doc_end
        sec = doc.Range(start, end)
        if num in SPLITTABLE_SECTIONS and sec.Tables.Count:
            _let_table_split(doc, sec)
        else:
            _keep_in_one_piece(sec)

    if DEBUG:
        doc.Repaginate()
        for num, first, last in page_report(doc):
            print(f"[word_layout] section {num:>2}: page {first} - {last}")