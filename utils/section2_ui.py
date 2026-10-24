"""
MSDS Section 2 - ingredient breakdown (Common Name | Color Index No. | CAS No.)

The form keeps the rows in  self.section2_rows  as [(name, color_index, cas), ...]
A button on the right side of the Section 2 group opens a small dialog to edit them.
In the CAS column, separate several numbers with ';' (printed one per line).
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView)

HEADERS = ["Common Name", "Color Index No.", "CAS No."]


class Section2Dialog(QDialog):
    def __init__(self, parent, rows):
        super().__init__(parent)
        self.setWindowTitle("Ingredient Breakdown")
        self.resize(640, 420)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        hint = QLabel("Several CAS numbers in one row: separate them with ;")
        layout.addWidget(hint)

        for r in rows:
            self._add_row(*r)

        btns = QHBoxLayout()
        for text, fn in (("Add", lambda: self._add_row("", "", "", edit=True)),
                         ("Delete", self._delete_row),
                         ("↑", lambda: self._move(-1)),
                         ("↓", lambda: self._move(1))):
            b = QPushButton(text)
            b.clicked.connect(fn)
            btns.addWidget(b)
        btns.addStretch(1)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)

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
        self.table.setCurrentCell(t, self.table.currentColumn())

    def rows(self):
        out = []
        for r in range(self.table.rowCount()):
            item = tuple((self.table.item(r, c).text() if self.table.item(r, c) else "").strip()
                         for c in range(3))
            if any(item):
                out.append(item)
        return out


# --------------------------------------------------------------------------
# form helpers (call these from the MSDS form module)
# --------------------------------------------------------------------------
def get_rows(form):
    return list(getattr(form, "section2_rows", []))


def set_rows(form, rows):
    form.section2_rows = list(rows)
    _refresh_button(form)


def _refresh_button(form):
    btn = getattr(form, "section2_btn", None)
    if btn is not None:
        n = len(form.section2_rows)
        btn.setText(f"Ingredient Breakdown ({n})" if n else "Ingredient Breakdown")


def _open_dialog(form):
    dlg = Section2Dialog(form, getattr(form, "section2_rows", []))
    if dlg.exec():
        set_rows(form, dlg.rows())


def build_group(form):
    """Replaces create_form_group("2) Composition/Information on Ingredients", ...)"""
    if not hasattr(form, "section2_rows"):
        form.section2_rows = []

    group = QGroupBox("2) Composition/Information on Ingredients")
    layout = QGridLayout(group)
    layout.setHorizontalSpacing(30)
    layout.setContentsMargins(20, 25, 20, 20)

    layout.addWidget(QLabel("Details:"), 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(form.composition_input, 0, 1)

    form.section2_btn = QPushButton()
    form.section2_btn.clicked.connect(lambda: _open_dialog(form))
    layout.addWidget(form.section2_btn, 0, 2, Qt.AlignmentFlag.AlignTop)
    _refresh_button(form)
    return group