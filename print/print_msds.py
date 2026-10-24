from PyQt6.QtCore import QBuffer, QIODevice, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog, QLabel
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from alert import window_alert
from db import db_con
from print import word_msds          # Word COM filler (word_msds.py)
from utils import abs_path


class FileMSDS(QWidget):
    # emitted from the Word worker thread -> handled on the GUI thread
    _pdf_ready = pyqtSignal(object, object)     # (msds_id, Future)
    _print_done = pyqtSignal(object)            # Future

    def __init__(self):
        super().__init__()
        self._pdf_ready.connect(self._on_pdf_ready)
        self._print_done.connect(self._on_print_done)
        word_msds.warm_up()      # no-op if main already did it
        self.setWindowTitle("Material Safety Data Sheet Preview")
        self.setWindowIcon(QIcon(abs_path.resource("img/icon.ico")))
        main_layout = QVBoxLayout(self)

        # PDF Document + Viewer
        self.pdf_doc = QPdfDocument(self)
        self.pdf_viewer = QPdfView(self)
        self.pdf_viewer.setDocument(self.pdf_doc)

        # Scrollable view with multiple pages
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomMode(QPdfView.ZoomMode.FitToWidth)

        dpi = 96
        letter_width = int(8.5 * dpi)  # 816 px
        self.pdf_viewer.setFixedWidth(letter_width)

        self.file_name = None
        self.msds_id = None
        self.pdf_bytes = None          # cached so Download doesn't re-launch Word

        btn_download = self.btn_download = QPushButton("Download")
        btn_print = self.btn_print = QPushButton("Print")
        btn_download.clicked.connect(lambda: self.download_pdf(self.msds_id, self.file_name))
        btn_print.clicked.connect(self.print_pdf)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(btn_download)
        button_layout.addSpacing(20)
        button_layout.addWidget(btn_print)
        button_layout.addStretch(1)

        btn_download.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: semi-bold;
                padding: 8px 16px;
                border: 1px solid #388E3C;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #45A049; }
            QPushButton:pressed { background-color: #397D3A; }
        """)
        btn_print.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: semi-bold;
                padding: 8px 16px;
                border: 1px solid #1976D2;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #1E88E5; }
            QPushButton:pressed { background-color: #1565C0; }
        """)

        main_layout.addLayout(button_layout)

        self.status_label = QLabel("Preparing document…")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        main_layout.addWidget(self.status_label)

        viewer_container = QHBoxLayout()
        viewer_container.addStretch(1)
        viewer_container.addWidget(self.pdf_viewer)
        viewer_container.addStretch(1)
        main_layout.addLayout(viewer_container)

        self.print_action = QAction(self)
        self.print_action.setShortcut("Ctrl+P")
        self.print_action.triggered.connect(self.print_pdf)
        self.addAction(self.print_action)

    # ------------------------------------------------------------------
    def _load_data(self, msds_id):
        return (db_con.get_single_msds_data(msds_id),
                db_con.get_single_msds_section9(msds_id),
                db_con.get_single_msds_section2(msds_id))

    def generate_pdf(self, msds_id):
        """Returns PDF bytes. Template (DC / MB1 / MB2) is picked automatically."""
        row, section9, section2 = self._load_data(msds_id)
        return word_msds.render_pdf_bytes(row, section9, section2)

    def _set_busy(self, busy, text="Preparing document…"):
        self.status_label.setText(text)
        self.status_label.setVisible(busy)
        self.btn_download.setEnabled(not busy)
        self.btn_print.setEnabled(not busy)

    def show_pdf_preview(self, msds_id, filename):
        self.file_name = filename
        self.msds_id = msds_id
        self.pdf_bytes = None
        self._set_busy(True)

        row, section9, section2 = self._load_data(msds_id)
        fut = word_msds.render_pdf_async(row, section9, section2)      # returns immediately
        fut.add_done_callback(lambda f, mid=msds_id: self._pdf_ready.emit(mid, f))

    def _on_pdf_ready(self, msds_id, fut):
        if msds_id != self.msds_id:          # user already opened another record
            return
        self._set_busy(False)
        try:
            self.pdf_bytes = fut.result()
        except Exception as e:
            window_alert.show_message(self, "Preview Error", f"Could not build the MSDS: {e}",
                                      icon_type="critical")
            return

        self.buffer = QBuffer()  # keep as attribute so it isn't garbage collected
        self.buffer.setData(self.pdf_bytes)
        self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.pdf_doc.load(self.buffer)
        self.pdf_viewer.setZoomMode(QPdfView.ZoomMode.FitToWidth)

    def download_pdf(self, msds_id, filename):
        if not self.pdf_bytes:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", filename, "PDF Files (*.pdf)")
        if not file_path:  # user cancelled
            return None
        if not file_path.endswith(".pdf"):
            file_path += ".pdf"

        with open(file_path, "wb") as f:
            f.write(self.pdf_bytes)

        window_alert.show_message(self, "Success", "File downloaded!", icon_type="info")

    def print_pdf(self):
        """Pick the printer with Qt's dialog, print through Word (pywin32)."""
        try:
            if not self.msds_id:
                return

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Print Material Safety Data Sheet")
            if not dialog.exec():
                return

            row, section9, section2 = self._load_data(self.msds_id)
            self._set_busy(True, "Sending to printer…")
            fut = word_msds.print_msds_async(row, section9, section2,
                                             printer_name=printer.printerName(),
                                             copies=printer.copyCount())
            fut.add_done_callback(self._print_done.emit)
        except Exception as e:
            self._set_busy(False)
            window_alert.show_message(self, "Print Error", f"An error occurred during printing: {e}",
                                      icon_type="critical")

    def _on_print_done(self, fut):
        self._set_busy(False)
        try:
            fut.result()
        except Exception as e:
            window_alert.show_message(self, "Print Error", f"An error occurred during printing: {e}",
                                      icon_type="critical")