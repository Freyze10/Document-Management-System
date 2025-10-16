import io
from datetime import datetime

from PyQt6.QtCore import QBuffer, QIODevice, QSize, Qt, QPointF
from PyQt6.QtGui import QIcon, QPainter
from PyQt6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPageSize, QPageLayout, QAction

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from alert import window_alert
from utils import abs_path
from db import db_con


class FileRowell(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Certificate of Inspection Preview")
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
        self.field_result = None

        btn_download = QPushButton("Download")
        btn_print = QPushButton("Print")
        btn_download.clicked.connect(self.download_pdf)
        btn_print.clicked.connect(self.print_pdf)

        # Put them in a horizontal layout and center
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
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #397D3A;
            }
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
        viewer_container.addStretch(1)
        viewer_container.addWidget(self.pdf_viewer)
        viewer_container.addStretch(1)
        main_layout.addLayout(viewer_container)

        # Keyboard shortcut
        self.print_action = QAction(self)
        self.print_action.setShortcut("Ctrl+P")
        self.print_action.triggered.connect(self.print_pdf)
        self.addAction(self.print_action)

    def generate_pdf(self, coa_id, is_rrf=False):
        """Generate PDF from Rowell inspection data"""
        field_result = db_con.get_single_coa_data(coa_id)
        properties_table_result = db_con.get_packageworld_rowell_properties(coa_id)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
        )

        styles = getSampleStyleSheet()

        # Custom styles
        styles.add(ParagraphStyle(
            name="Title",
            fontName="Times-Bold",
            fontSize=14,
            leading=16,
            alignment=TA_CENTER,
            spaceAfter=4
        ))

        styles.add(ParagraphStyle(
            name="Subtitle",
            fontName="Times-Bold",
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=20
        ))

        styles.add(ParagraphStyle(
            name="FieldLabel",
            fontName="Times-Roman",
            fontSize=11,
            leading=14,
            spaceAfter=8
        ))

        styles.add(ParagraphStyle(
            name="SectionHeader",
            fontName="Times-Bold",
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=12,
            spaceBefore=12
        ))

        styles.add(ParagraphStyle(
            name="SmallText",
            fontName="Times-Roman",
            fontSize=9,
            leading=11,
            spaceAfter=6
        ))

        content = []

        # Header
        content.append(Paragraph("CERTIFICATE OF INSPECTION", styles["Title"]))
        content.append(Paragraph("PVC-FREE COMPOUND FOOD APPROVED", styles["Subtitle"]))
        content.append(Spacer(1, 10))

        # Customer Information
        content.append(Paragraph(
            f"Customer: <b>{(field_result[1])}</b>",
            styles["FieldLabel"]
        ))

        content.append(Paragraph(
            f"Product Name: {properties_table_result[0][0]}",
            styles["FieldLabel"]
        ))

        content.append(Paragraph(
            f"Code: {field_result[2]}",
            styles["FieldLabel"]
        ))

        content.append(Paragraph(
            f"Lot Number: {field_result[3]}",
            styles["FieldLabel"]
        ))

        content.append(Paragraph(
            f"Total Quantity: {field_result[6]}",
            styles["FieldLabel"]
        ))

        # Format manufacturing date
        mfg_date = field_result['manufacturing_date']
        if isinstance(mfg_date, datetime):
            mfg_date_str = mfg_date.strftime('%B %d, %Y')
        else:
            mfg_date_str = mfg_date.strftime('%B %d, %Y')

        content.append(Paragraph(
            f"Manufacturing Date: {mfg_date_str}",
            styles["FieldLabel"]
        ))

        content.append(Paragraph(
            f"Shelf Life: {field_result[12]}",
            styles["FieldLabel"]
        ))

        content.append(Paragraph(
            "*Shelf life is stated as a maximum from date of production when the product is stored in unbroken packaging.",
            styles["SmallText"]
        ))

        content.append(Spacer(1, 20))

        # Physical/Typical Properties Section
        content.append(Paragraph("PHYSICAL / TYPICAL PROPERTIES", styles["SectionHeader"]))
        content.append(Spacer(1, 10))

        # Build table data
        table_data = [["", "New Delivery", "Standard", "Method Used"]]

        for row in properties_table_result[1:]:  # Fixed typo: rows -> row
            table_data.append([
                row[0],
                row[1],
                row[2],
                row[3]
            ])

        # Calculate column widths
        page_width = letter[0] - 100
        col_widths = [
            page_width * 0.25,  # Property name
            page_width * 0.25,  # New Delivery
            page_width * 0.25,  # Standard
            page_width * 0.25  # Method
        ]

        # Create table
        properties_table = Table(table_data, colWidths=col_widths, hAlign="LEFT")
        properties_table.setStyle(TableStyle([
            # Header row
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),

            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),

            # Borders
            ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),

            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),

            # Vertical alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        content.append(properties_table)
        content.append(Spacer(1, 30))

        # Certification Section
        cert_date = field_result[9]
        if isinstance(cert_date, datetime):
            cert_date_str = cert_date.strftime('%B %d, %Y')
        else:
            cert_date_str = cert_date.strftime('%B %d, %Y')

        # Create underline for signature
        name_len = len(field_result[10])
        underline = "_" * max(25, name_len)

        content.append(Paragraph(
            f"Certified by: {underline}",
            styles["FieldLabel"]
        ))

        # Add indented name and title
        indent_style = ParagraphStyle(
            "Indent",
            parent=styles["FieldLabel"],
            leftIndent=80,
            spaceAfter=2
        )

        content.append(Paragraph(field_result[10], indent_style))
        content.append(Paragraph(properties_table_result[0][1], indent_style))
        content.append(Spacer(1, 10))

        content.append(Paragraph(
            f"Date: {cert_date_str}",
            styles["FieldLabel"]
        ))

        content.append(Spacer(1, 20))

        # Form number (bottom right)
        form_style = ParagraphStyle(
            "FormNumber",
            parent=styles["SmallText"],
            alignment=2  # Right align
        )
        content.append(Paragraph("FM00003A", form_style))

        # Build PDF
        doc.build(content)
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
