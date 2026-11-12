"""
After an MSDS is saved: ask "Download this MSDS / TDS to a shared folder?"

    +--------------------------------------------------+
    |  ✓ MSDS saved successfully                       |
    |  Download this MSDS / TDS to a shared folder?    |
    |                                                  |
    |  Folder     [ C:\\Users\\me\\Documents    ][Browse…]|
    |  File name  Trade name 1234.pdf                  |
    |                                                  |
    |                          [ Not now ] [ Download ]|
    +--------------------------------------------------+

* The first time the folder is the user's Documents folder.
* When the user picks another folder (Browse…) it is remembered and becomes the default next time.
* The file name is the SAME text the Records list passes to the print preview, so "Download" in the
  preview and this dialog give the same name. (Re-saving the same record overwrites its file.)
* The PDF is built through word_msds (DC / MB1 / MB2 template picked automatically), off the GUI thread.

Use from the main window, after the record is saved and the records table is reloaded:

    msds_export.offer_download(self, msds_id, updated=False)
"""
import os
import re

from PyQt6.QtCore import Qt, QSettings, QStandardPaths, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout)

from alert import window_alert
from db import db_con
from print import word_msds

_SETTINGS_KEY = "export/msds_dir"

DIALOG_QSS = """
    QDialog { background-color: #f8f9fa; font-family: 'Segoe UI', 'Inter', sans-serif; }
    QLabel { font-size: 13px; color: #495057; background: transparent; }
    QLabel#title { font-size: 18px; font-weight: 700; color: #1f7a3a; }
    QLabel#question { font-size: 15px; font-weight: 600; color: #1f3a5f; }
    QLabel#caption { font-size: 12px; font-weight: 700; color: #6c757d; }
    QLabel#fileName { font-size: 13px; font-weight: 600; color: #343a40; }
    QLabel#status { font-size: 12px; color: #6c757d; }
    QLabel#status[error="true"] { color: #dc3545; font-weight: 600; }
    QLineEdit { font-size: 13px; padding: 6px 10px; border: 1px solid #ced4da; border-radius: 6px;
                background-color: #ffffff; color: #343a40; min-height: 22px; }
    QPushButton { font-size: 13px; font-weight: 600; padding: 6px 18px; border-radius: 6px; min-height: 22px;
                  border: 1px solid #ced4da; background-color: #ffffff; color: #495057; }
    QPushButton:hover { background-color: #e9ecef; }
    QPushButton:disabled { color: #adb5bd; background-color: #f1f3f5; }
    QPushButton#primary { background-color: #28a745; border: none; color: #ffffff; min-width: 110px; }
    QPushButton#primary:hover { background-color: #218838; }
    QPushButton#primary:disabled { background-color: #a3d9b1; color: #f8f9fa; }
"""


# --------------------------------------------------------------------------
# remembered folder
# --------------------------------------------------------------------------
def _settings():
    return QSettings("MBPI", "MSDS")


def documents_dir():
    return (QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            or os.path.expanduser("~"))


def get_export_dir():
    """The folder used last time (picked by the user), or Documents the very first time."""
    saved = _settings().value(_SETTINGS_KEY, "", type=str)
    return os.path.normpath(saved) if saved else os.path.normpath(documents_dir())


def set_export_dir(path):
    """Remember `path` as the default folder for the next download."""
    _settings().setValue(_SETTINGS_KEY, os.path.normpath(path))


# --------------------------------------------------------------------------
# file name
# --------------------------------------------------------------------------
def _safe(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(name)).strip(" .")
    return name

def _with_tds(filename):
    """'... MSDS 11-12-2026'  ->  '... MSDS TDS 11-12-2026'  (only inserts TDS, name and date stay)"""
    if not filename or re.search(r"\bTDS\b", filename, re.IGNORECASE):
        return filename
    return re.sub(r"\bMSDS\b(?!.*\bMSDS\b)", "MSDS TDS", filename, count=1)


def preview_filename(window, msds_id):
    """The name the print preview uses: the text of the record's first cell in the Records list.
    (msds_cell_clicked passes exactly that text to open_msds_preview -> Download.)"""
    name = ""
    table = getattr(window, "msds_records_table", None)
    if table is not None:
        for r in range(table.rowCount()):
            item = table.item(r, 0)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == msds_id:
                name = item.text()
                break
    if not name.strip():                                    # list not available: same idea from the DB
        row = db_con.get_single_msds_data(msds_id)
        name = str(row[2] or "").strip() or str(row[1] or "").strip()
    name = _safe(_with_tds(name)) or f"MSDS_{msds_id}"
    return name if name.lower().endswith(".pdf") else name + ".pdf"


# --------------------------------------------------------------------------
# dialog
# --------------------------------------------------------------------------
class DownloadDialog(QDialog):
    _pdf_ready = pyqtSignal(object)          # Future, emitted from the Word worker thread

    def __init__(self, parent, msds_id, file_name, updated=False):
        super().__init__(parent)
        self.msds_id = msds_id
        self.file_name = file_name
        self.saved_path = None
        self._busy = False

        self.setWindowTitle("MSDS Saved")
        self.setStyleSheet(DIALOG_QSS)
        self.setMinimumWidth(620)
        self._pdf_ready.connect(self._on_pdf_ready)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 18)
        root.setSpacing(12)

        title = QLabel("✓  MSDS updated successfully" if updated else "✓  MSDS saved successfully")
        title.setObjectName("title")
        question = QLabel("Download this MSDS / TDS to a shared folder?")
        question.setObjectName("question")
        root.addWidget(title)
        root.addWidget(question)
        root.addSpacing(6)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        cap_folder = QLabel("Folder")
        cap_folder.setObjectName("caption")
        self.path_edit = QLineEdit(get_export_dir())
        self.path_edit.setReadOnly(True)
        self.path_edit.setToolTip(self.path_edit.text())
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(self._browse)
        grid.addWidget(cap_folder, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self.path_edit, 0, 1)
        grid.addWidget(self.browse_btn, 0, 2)

        cap_name = QLabel("File name")
        cap_name.setObjectName("caption")
        self.name_label = QLabel(file_name)
        self.name_label.setObjectName("fileName")
        self.name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        grid.addWidget(cap_name, 1, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self.name_label, 1, 1, 1, 2)
        root.addLayout(grid)

        self.status = QLabel("")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btns.addStretch(1)
        self.skip_btn = QPushButton("Not now")
        self.skip_btn.clicked.connect(self.reject)
        self.download_btn = QPushButton("Download")
        self.download_btn.setObjectName("primary")
        self.download_btn.setDefault(True)
        self.download_btn.clicked.connect(self._download)
        btns.addWidget(self.skip_btn)
        btns.addWidget(self.download_btn)
        root.addLayout(btns)

    # -- helpers ------------------------------------------------------------
    def _set_status(self, text, error=False):
        self.status.setText(text)
        self.status.setProperty("error", error)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def _set_busy(self, busy):
        self._busy = busy
        for b in (self.browse_btn, self.skip_btn, self.download_btn):
            b.setEnabled(not busy)

    def reject(self):                       # no closing (Esc / X) while the PDF is being built
        if not self._busy:
            super().reject()

    # -- actions ------------------------------------------------------------
    def _browse(self):
        start = self.path_edit.text() if os.path.isdir(self.path_edit.text()) else documents_dir()
        folder = QFileDialog.getExistingDirectory(self, "Select the folder to save the MSDS to", start)
        if folder:
            folder = os.path.normpath(folder)
            self.path_edit.setText(folder)
            self.path_edit.setToolTip(folder)
            set_export_dir(folder)           # the next default
            self._set_status("")

    def _download(self):
        self._set_busy(True)
        self._set_status("Preparing the document…")
        try:
            row = db_con.get_single_msds_data(self.msds_id)
            section9 = db_con.get_single_msds_section9(self.msds_id)
            section2 = db_con.get_single_msds_section2(self.msds_id)
            fut = word_msds.render_pdf_async(row, section9, section2)
        except Exception as e:
            self._set_busy(False)
            self._set_status(f"Could not build the MSDS: {e}", error=True)
            return
        fut.add_done_callback(self._pdf_ready.emit)

    def _on_pdf_ready(self, fut):
        try:
            data = fut.result()
            folder = self.path_edit.text()
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, self.file_name)
            with open(path, "wb") as f:
                f.write(data)
        except Exception as e:
            self._set_busy(False)
            self._set_status(f"Could not save the file: {e}", error=True)
            return
        set_export_dir(folder)               # also covers "typed nothing, just kept the default"
        self.saved_path = path
        self._set_busy(False)
        self.accept()


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------
def offer_download(window, msds_id, updated=False):
    """Show the 'download to a shared folder' dialog for a record that was just saved.
    Returns the saved file path, or None if the user chose 'Not now'."""
    dlg = DownloadDialog(window, msds_id, preview_filename(window, msds_id), updated)
    if dlg.exec() and dlg.saved_path:
        window_alert.show_message(window, "Downloaded", f"Saved to:\n{dlg.saved_path}", icon_type="info")
        return dlg.saved_path
    return None