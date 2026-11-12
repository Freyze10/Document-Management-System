"""
MSDS Section 2 - Composition / Information on Ingredients

    2) Composition/Information on Ingredients
    ---------------------------------------------------------------
    Details:   [ text box (full width)                              ]

    [ Ingredient Breakdown  (6)              [ Edit ] [ + New Entry ] ]
    [ Common Name        | Color Index No. | CAS No.                  ]
    [ Titanium Dioxide   | PW 6            | 13463-67-7               ]
    [ ...                                                           ]

* [+ New Entry]  small dialog: type one ingredient, "Add & New" keeps it open for the next one.
* [Edit]         bigger dialog: edit cells, add / delete / reorder rows (Ctrl+S = Save).
* The preview grows with its rows (up to MAX_VISIBLE, then it scrolls); the form page
  itself is already scrollable.

Data lives in  form.section2_rows = [(name, color_index, cas), ...]
In the CAS column, separate several numbers with ';' (printed one per line in the MSDS).

API (unchanged):  build_group(form[, wire]) / get_rows(form) / set_rows(form, rows)
"""
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (QAbstractItemView, QDialog, QFormLayout, QFrame, QGridLayout, QGroupBox,
                             QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout)

HEADERS = ["Common Name", "Color Index No.", "CAS No."]
HEADER_H = 36         # px, table header
ROW_H = 34            # px, one table row
MAX_VISIBLE = 8       # rows shown before the preview starts scrolling

# same palette as the rest of the form
PANEL_QSS = """
    QFrame#s2Panel { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; }
    QFrame#s2Header { background-color: #f1f6fb; border: none; border-bottom: 1px solid #dee2e6;
                      border-top-left-radius: 8px; border-top-right-radius: 8px; }
    QLabel#s2Title { font-size: 14px; font-weight: 700; color: #2c3e50; background: transparent; }
    QLabel#s2Badge { background-color: #007bff; color: #ffffff; border-radius: 10px;
                     padding: 1px 9px; font-size: 12px; font-weight: 700; }
    QLabel#s2Empty { color: #868e96; font-size: 13px; background-color: #ffffff;
                     border: 2px dashed #ced4da; border-radius: 8px; padding: 22px; margin: 12px; }
    QPushButton { font-size: 13px; font-weight: 600; border-radius: 6px; padding: 6px 16px; min-height: 22px; }
    QPushButton#s2New { background-color: #007bff; color: #ffffff; border: none; }
    QPushButton#s2New:hover { background-color: #0056b3; }
    QPushButton#s2New:pressed { background-color: #004085; }
    QPushButton#s2Edit { background-color: #ffffff; color: #007bff; border: 1px solid #007bff; }
    QPushButton#s2Edit:hover { background-color: #e9f5ff; }
    QPushButton#s2Edit:disabled { color: #adb5bd; border: 1px solid #ced4da; background-color: #f8f9fa; }
    QTableWidget#s2Preview { background-color: #ffffff; alternate-background-color: #f7faff; border: none;
                             font-size: 13px; color: #343a40; gridline-color: #eef0f2; }
    QTableWidget#s2Preview::item { padding: 0px 10px; }
    QHeaderView::section { background-color: #ffffff; color: #495057; font-size: 12px; font-weight: 700;
                           padding: 0px 10px; border: none; border-bottom: 2px solid #007bff; }
"""

DIALOG_QSS = """
    QDialog { background-color: #f8f9fa; font-family: 'Inter', 'Segoe UI', sans-serif; }
    QLabel { background: transparent; color: #495057; font-size: 13px; font-weight: 600; }
    QLabel#dlgTitle { font-size: 18px; font-weight: 700; color: #2c3e50; padding-bottom: 6px;
                      border-bottom: 3px solid #007bff; }
    QLabel#dlgHint { font-size: 12px; font-weight: 400; color: #868e96; }
    QLabel#dlgOk { font-size: 12px; font-weight: 600; color: #28a745; }
    QLineEdit { font-size: 13px; padding: 6px 10px; border: 1px solid #ced4da; border-radius: 6px;
                background-color: #ffffff; color: #343a40; min-height: 22px; }
    QLineEdit:focus { border: 1px solid #007bff; background-color: #e9f5ff; }
    QTableWidget { background-color: #ffffff; alternate-background-color: #f7faff; border: 1px solid #ced4da;
                   border-radius: 6px; font-size: 13px; color: #343a40; gridline-color: #eef0f2;
                   selection-background-color: #cfe8ff; selection-color: #212529; }
    QTableWidget::item { padding: 0px 8px; }
    QTableWidget QLineEdit { padding: 0px 6px; border: 1px solid #007bff; border-radius: 0px; min-height: 0px; }
    QHeaderView::section { background-color: #e9f5ff; color: #2c3e50; font-size: 12px; font-weight: 700;
                           padding: 0px 10px; border: none; border-bottom: 2px solid #007bff; }
    QPushButton { font-size: 13px; font-weight: 600; padding: 6px 16px; border-radius: 6px; min-height: 22px;
                  border: 1px solid #ced4da; background-color: #ffffff; color: #495057; }
    QPushButton:hover { background-color: #e9ecef; }
    QPushButton#primary { background-color: #007bff; border: none; color: #ffffff; }
    QPushButton#primary:hover { background-color: #0056b3; }
    QPushButton#success { background-color: #28a745; border: none; color: #ffffff; }
    QPushButton#success:hover { background-color: #218838; }
    QPushButton#danger { color: #dc3545; border: 1px solid #dc3545; }
    QPushButton#danger:hover { background-color: #ffebeb; }
"""


def _norm(rows):
    """-> list of (name, color_index, cas) strings, None-safe, empty rows dropped."""
    out = []
    for r in rows or []:
        t = tuple("" if v is None else str(v).strip() for v in tuple(r)[:3])
        t = t + ("",) * (3 - len(t))
        if any(t):
            out.append(t)
    return out


# --------------------------------------------------------------------------
# dialog 1: add ONE ingredient (quick entry)
# --------------------------------------------------------------------------
class NewEntryDialog(QDialog):
    """Type an ingredient. 'Add & New' saves it and clears the fields for the next one."""

    def __init__(self, parent, on_add):
        super().__init__(parent)
        self._on_add = on_add
        self._count = 0
        self.setWindowTitle("New Ingredient Entry")
        self.setStyleSheet(DIALOG_QSS)
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        title = QLabel("New Ingredient Entry")
        title.setObjectName("dlgTitle")
        root.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g. Titanium Dioxide")
        self.color_index = QLineEdit()
        self.color_index.setPlaceholderText("e.g. PW 6   (or N/A)")
        self.cas = QLineEdit()
        self.cas.setPlaceholderText("e.g. 13463-67-7   (several: separate with ;)")
        form.addRow("Common Name *", self.name)
        form.addRow("Color Index No.", self.color_index)
        form.addRow("CAS No.", self.cas)
        root.addLayout(form)

        self.status = QLabel("")
        self.status.setObjectName("dlgOk")
        root.addWidget(self.status)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btns.addStretch(1)
        cancel = QPushButton("Close")
        cancel.clicked.connect(self.reject)
        add_new = QPushButton("Add && New")
        add_new.setObjectName("success")
        add_new.clicked.connect(self._add_and_new)
        add = QPushButton("Add")
        add.setObjectName("primary")
        add.clicked.connect(self._add_and_close)
        btns.addWidget(cancel)
        btns.addWidget(add_new)
        btns.addWidget(add)
        root.addLayout(btns)

        # Enter walks through the fields, Enter on the last one = Add & New
        self.name.returnPressed.connect(self.color_index.setFocus)
        self.color_index.returnPressed.connect(self.cas.setFocus)
        self.cas.returnPressed.connect(self._add_and_new)
        self.name.textChanged.connect(lambda: self.name.setStyleSheet(""))

    def _try_add(self):
        name = self.name.text().strip()
        if not name:
            self.name.setStyleSheet("border: 1px solid #dc3545; background-color: #ffebeb;")
            self.name.setFocus()
            return False
        self._on_add((name, self.color_index.text().strip(), self.cas.text().strip()))
        self._count += 1
        self.status.setText(f"✓ Added: {name}   ({self._count} added)")
        return True

    def _add_and_new(self):
        if self._try_add():
            for w in (self.name, self.color_index, self.cas):
                w.clear()
            self.name.setFocus()

    def _add_and_close(self):
        if self._try_add():
            self.accept()


# --------------------------------------------------------------------------
# dialog 2: edit / delete / reorder everything
# --------------------------------------------------------------------------
class Section2Dialog(QDialog):
    def __init__(self, parent, rows):
        super().__init__(parent)
        self.setWindowTitle("Edit Ingredient Breakdown")
        self.setStyleSheet(DIALOG_QSS)
        self.resize(780, 480)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(12)

        title = QLabel("Edit Ingredient Breakdown")
        title.setObjectName("dlgTitle")
        root.addWidget(title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(ROW_H)
        self.table.horizontalHeader().setFixedHeight(HEADER_H)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        root.addWidget(self.table, stretch=1)

        hint = QLabel("Double-click a cell to edit it.   Several CAS numbers in one row: separate them with  ;")
        hint.setObjectName("dlgHint")
        root.addWidget(hint)

        for r in _norm(rows):
            self._add_row(*r)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        for text, fn, name in (("+ Add Row", lambda: self._add_row("", "", "", edit=True), "primary"),
                               ("Delete", self._delete_row, "danger"),
                               ("↑ Up", lambda: self._move(-1), ""),
                               ("↓ Down", lambda: self._move(1), "")):
            b = QPushButton(text)
            if name:
                b.setObjectName(name)
            b.clicked.connect(fn)
            btns.addWidget(b)
        btns.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setObjectName("success")
        save.setToolTip("Ctrl+S")
        save.clicked.connect(self.accept)
        btns.addWidget(cancel)
        btns.addWidget(save)
        root.addLayout(btns)

        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.accept)

    def _add_row(self, name, color_index, cas, edit=False):
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, v in enumerate((name, color_index, cas)):
            self.table.setItem(r, c, QTableWidgetItem(v))
        if edit:
            self.table.setCurrentCell(r, 0)
            self.table.editItem(self.table.item(r, 0))

    def _delete_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)

    def _move(self, delta):
        r = self.table.currentRow()
        t = r + delta
        if r < 0 or t < 0 or t >= self.table.rowCount():
            return
        for c in range(3):
            a, b = self.table.item(r, c), self.table.item(t, c)
            ta, tb = a.text(), b.text()
            a.setText(tb)
            b.setText(ta)
        self.table.setCurrentCell(t, max(self.table.currentColumn(), 0))

    def rows(self):
        if self.table.state() == QAbstractItemView.State.EditingState:
            self.table.setFocus()                    # commit a cell that is still being edited
        return _norm([[(self.table.item(r, c).text() if self.table.item(r, c) else "")
                       for c in range(3)] for r in range(self.table.rowCount())])


# --------------------------------------------------------------------------
# data helpers (used by the MSDS form module)
# --------------------------------------------------------------------------
def get_rows(form):
    return list(getattr(form, "section2_rows", []))


def set_rows(form, rows):
    form.section2_rows = _norm(rows)
    _refresh(form)


def _open_new_entry(form):
    NewEntryDialog(form, lambda row: set_rows(form, get_rows(form) + [row])).exec()


def _open_edit(form):
    dlg = Section2Dialog(form, get_rows(form))
    if dlg.exec():
        set_rows(form, dlg.rows())


# --------------------------------------------------------------------------
# inline panel
# --------------------------------------------------------------------------
def _refresh(form):
    table = getattr(form, "section2_table", None)
    if table is None:                                # group not built yet
        return
    rows = form.section2_rows
    n = len(rows)

    table.setRowCount(n)
    for r, (name, ci, cas) in enumerate(rows):
        shown_cas = ",   ".join(p.strip() for p in cas.replace("\n", ";").split(";") if p.strip())
        for c, v in enumerate((name, ci, shown_cas)):
            item = QTableWidgetItem(v)
            item.setToolTip(v)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(r, c, item)

    # as tall as its rows, capped at MAX_VISIBLE (then it scrolls)
    table.setFixedHeight(HEADER_H + min(max(n, 1), MAX_VISIBLE) * ROW_H + 2)
    table.setVisible(n > 0)
    form.section2_empty.setVisible(n == 0)
    form.section2_badge.setText(f"{n} {'entry' if n == 1 else 'entries'}")
    form.section2_badge.setVisible(n > 0)
    form.section2_edit_btn.setEnabled(n > 0)


def build_group(form, wire=None):
    """The finished '2) Composition/Information on Ingredients' group box.
    `wire` (optional) = the form's helper that hooks validation / auto-height to a field."""
    if not hasattr(form, "section2_rows"):
        form.section2_rows = []

    group = QGroupBox("2) Composition/Information on Ingredients")
    grid = QGridLayout(group)
    grid.setHorizontalSpacing(16)
    grid.setVerticalSpacing(14)
    grid.setContentsMargins(20, 4, 20, 20)
    grid.setColumnStretch(0, 1)

    # ---- row 0: Details (full width, like the other single-box sections) -------
    grid.addWidget(form.composition_input, 0, 0)
    if wire:
        wire(form.composition_input)

    # ---- row 1: breakdown panel, full width ------------------------------------
    panel = QFrame()
    panel.setObjectName("s2Panel")
    panel.setStyleSheet(PANEL_QSS)
    panel_l = QVBoxLayout(panel)
    panel_l.setContentsMargins(0, 0, 0, 0)
    panel_l.setSpacing(0)

    header = QFrame()
    header.setObjectName("s2Header")
    header.setFixedHeight(54)
    head = QHBoxLayout(header)
    head.setContentsMargins(16, 10, 12, 10)
    head.setSpacing(10)
    title = QLabel("Ingredient Breakdown")
    title.setObjectName("s2Title")
    form.section2_badge = QLabel("0 entries")
    form.section2_badge.setObjectName("s2Badge")
    form.section2_edit_btn = QPushButton("Edit")
    form.section2_edit_btn.setObjectName("s2Edit")
    form.section2_edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    form.section2_edit_btn.clicked.connect(lambda: _open_edit(form))
    form.section2_btn = QPushButton("+ New Entry")        # kept name: the main "add" button
    form.section2_btn.setObjectName("s2New")
    form.section2_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    form.section2_btn.clicked.connect(lambda: _open_new_entry(form))
    head.addWidget(title)
    head.addWidget(form.section2_badge)
    head.addStretch(1)
    head.addWidget(form.section2_edit_btn)
    head.addWidget(form.section2_btn)
    panel_l.addWidget(header)

    form.section2_empty = QLabel("No ingredients listed yet.\nClick  + New Entry  to add the first one.")
    form.section2_empty.setObjectName("s2Empty")
    form.section2_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
    panel_l.addWidget(form.section2_empty)

    t = QTableWidget(0, 3)
    t.setObjectName("s2Preview")
    t.setHorizontalHeaderLabels(HEADERS)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(ROW_H)
    hh = t.horizontalHeader()
    hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    hh.setFixedHeight(HEADER_H)
    hh.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.setWordWrap(False)
    t.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    t.cellDoubleClicked.connect(lambda *_: _open_edit(form))
    form.section2_table = t
    panel_l.addWidget(t)

    grid.addWidget(panel, 1, 0)

    _refresh(form)
    return group