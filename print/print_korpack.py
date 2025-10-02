import platform
import io
from PyQt6.QtCore import QBuffer, QIODevice, QSize, Qt, QPointF
from PyQt6.QtGui import QPainter, QPageSize, QPageLayout, QAction, QIcon
from PyQt6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Indenter
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from alert import window_alert
from db import db_con
from print.pdf_header import add_first_page_header
from utils import abs_path


def split_by_comma(s):
    return [part.strip() for part in s.split(',')]


class FileKorpack(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COA-TERUMO Preview")
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
        self.coa_id = None

        btn_download = QPushButton("Download")
        btn_print = QPushButton("Print")
        btn_download.clicked.connect(lambda: self.download_pdf(self.coa_id, self.file_name))
        btn_print.clicked.connect(self.print_pdf)

        # Put them in a horizontal layout and center
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(btn_download)
        button_layout.addSpacing(20)  # space between buttons
        button_layout.addWidget(btn_print)
        button_layout.addStretch(1)

        btn_download.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;  /* Green */
                        color: white;
                        font-size: 14px;
                        font-weight: semi-bold;
                        padding: 8px 16px;
                        border: 1px solid #388E3C;
                        border-radius: 6px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #45A049;
                    }
                    QPushButton:pressed {
                        background-color: #397D3A;
                    }
                """)

        # Blue Print button
        btn_print.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;  /* Blue */
                        color: white;
                        font-size: 14px;
                        font-weight: semi-bold;
                        padding: 8px 16px;
                        border: 1px solid #1976D2;
                        border-radius: 6px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #1E88E5;
                    }
                    QPushButton:pressed {
                        background-color: #1565C0;
                    }
                """)

        main_layout.addLayout(button_layout)
        # Center the viewer using a horizontal layout
        viewer_container = QHBoxLayout()
        viewer_container.addStretch(1)  # left stretch
        viewer_container.addWidget(self.pdf_viewer)
        viewer_container.addStretch(1)  # right stretch
        main_layout.addLayout(viewer_container)

        self.print_action = QAction(self)
        self.print_action.setShortcut("Ctrl+P")
        self.print_action.triggered.connect(self.print_pdf)
        self.addAction(self.print_action)

    def generate_pdf(self, coa_id, is_rrf=False):
        field_result = db_con.get_single_coa_data(coa_id)
        korpack_res = db_con.get_single_korpack_data(coa_id)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50, leftMargin=50, topMargin=90, bottomMargin=40
        )
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        bold_center = ParagraphStyle(
            'BoldCenter', parent=normal,
            fontName='Helvetica-Bold', fontSize=16,
            alignment=TA_CENTER)
        left_label = ParagraphStyle('Label', parent=normal, fontName='Helvetica-Bold', fontSize=10, alignment=TA_LEFT)
        field_val = ParagraphStyle('Field', parent=normal, fontSize=10, alignment=TA_LEFT)
        footer_name = ParagraphStyle('footerName', parent=normal, fontName='Helvetica-Bold', fontSize=11)
        footer_role = ParagraphStyle('footerRole', parent=normal, fontSize=10)
        sig_line_style = ParagraphStyle('SigLine', parent=normal, fontSize=10, alignment=TA_LEFT)
        form_style = ParagraphStyle('Form', parent=normal, fontSize=9, alignment=TA_RIGHT)

        content = []
        # HEADER
        content.append(Paragraph("CERTIFICATE OF ANALYSIS", bold_center))
        content.append(Spacer(1, 12))

        # General Description header
        content.append(Paragraph("General Description", left_label))
        content.append(Spacer(1, 6))

        # Description Details Table (all fields under General Description)
        quantity_str = f"{float(field_result[6]):.2f} kg." if field_result[6] else ""
        manuf_date_str = korpack_res[3].strftime('%B %d, %Y') if korpack_res[3] else ""
        delivery_date_str = field_result[7].strftime('%B %d, %Y') if field_result[7] else ""
        description_data = [
            ["Product Name:", korpack_res[2]],
            ["Product Lot No.:", field_result[3]],
            ["Product Quantity:", quantity_str],
            ["Manufacturing Date:", manuf_date_str],
            ["Delivery Date:", delivery_date_str],
            ["Physical Form:", korpack_res[4]],
            ["Heat Stability:", korpack_res[5]],
            ["Light fastness:", korpack_res[6]],
            ["Migration:", korpack_res[7]],
            ["Swatch dosage:", korpack_res[8]],
            ["Product Applications:", korpack_res[9]],
            ["Packaging Form:", korpack_res[10]],
        ]
        description_table = Table(description_data, colWidths=[140, 310])
        description_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (1, 0), (1, -1), 10),
        ]))
        content.append(description_table)
        content.append(Spacer(1, 12))

        # Regulatory Information
        regulatory_info = korpack_res[11].replace('\n', '<br/>') if korpack_res[11] else ""
        content.append(Paragraph("Regulatory Information", left_label))
        content.append(Spacer(1, 6))
        content.append(Paragraph(regulatory_info, field_val))
        content.append(Spacer(1, 16))

        # Footer
        name_val = korpack_res[12]
        pos_val = korpack_res[13]
        content.append(Paragraph("Inspected & Approved by:", left_label))
        content.append(Spacer(1, 5))
        content.append(Paragraph("_______________________________________", sig_line_style))
        content.append(Spacer(1, 12))
        content.append(Paragraph(f"    {name_val}", normal))
        if pos_val:
            content.append(Paragraph(f"        {pos_val}", normal))
        content.append(Spacer(1, 20))
        content.append(Paragraph("FM00003A", form_style))

        doc.build(content, onFirstPage=add_first_page_header)
        buffer.seek(0)
        return buffer.getvalue()

    def show_pdf_preview(self, coa_id, filename, is_rrf):
        self.file_name = filename
        self.coa_id = coa_id
        pdf_bytes = self.generate_pdf(coa_id, is_rrf)
        # Wrap the PDF bytes in a QBuffer
        self.buffer = QBuffer()  # keep it as an instance attribute so it's not garbage collected
        self.buffer.setData(pdf_bytes)
        self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)

        # Load PDF from QBuffer
        self.pdf_doc.load(self.buffer)
        self.pdf_viewer.setZoomMode(QPdfView.ZoomMode.FitToWidth)

    def download_pdf(self, coa_id, filename):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF",
            filename,  # default name
            "PDF Files (*.pdf)"
        )

        if not file_path:  # user cancelled
            return None

        if not file_path.endswith(".pdf"):
            file_path += ".pdf"

        pdf_bytes = self.generate_pdf(coa_id)
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        window_alert.show_message(self, "Success", "File downloaded!", icon_type="info")

    def print_pdf(self):
        try:
            if not self.pdf_doc or self.pdf_doc.pageCount() == 0:
                return  # nothing to print

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)

            # Set printer page size using QPageLayout
            page_layout = QPageLayout()
            page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
            printer.setPageLayout(page_layout)

            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Print Certificate of Analysis")

            if dialog.exec():
                painter = QPainter(printer)
                render_options = QPdfDocumentRenderOptions()

                # Choose a sufficiently high DPI for rendering the PDF to an image
                # 600 DPI is a good balance for print quality
                render_dpi = 600

                for i in range(self.pdf_doc.pageCount()):
                    if i > 0:
                        printer.newPage()

                    pdf_page_size_points = self.pdf_doc.pagePointSize(i)

                    render_dpi = 300
                    image_render_width_pixels = int(pdf_page_size_points.width() / 72.0 * render_dpi)
                    image_render_height_pixels = int(pdf_page_size_points.height() / 72.0 * render_dpi)

                    pdf_image = self.pdf_doc.render(
                        i,
                        QSize(image_render_width_pixels, image_render_height_pixels),
                        render_options
                    )

                    if not pdf_image.isNull():
                        # Use the full page, not the printable area
                        full_page_pixels = printer.paperRect(QPrinter.Unit.DevicePixel)

                        scaled_image = pdf_image.scaled(
                            full_page_pixels.size().toSize(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )

                        # Align to the top (no margin)
                        x = full_page_pixels.x() + (full_page_pixels.width() - scaled_image.width()) / 2
                        y = full_page_pixels.y()  # start at the very top

                        painter.drawImage(QPointF(x, y), scaled_image)
                painter.end()
        except Exception as e:
            print(f"An error occurred during printing: {e}")
