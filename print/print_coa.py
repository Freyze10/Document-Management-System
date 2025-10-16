import platform
import io
import re

from PyQt6.QtCore import QBuffer, QIODevice, QSize, Qt, QPointF
from PyQt6.QtGui import QPainter, QPageSize, QPageLayout, QAction, QIcon
from PyQt6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from alert import window_alert
from db import db_con
from print.pdf_header import add_first_page_header, add_coa_header
from utils import abs_path


class FileCOA(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Certificate of Analysis Preview")
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
        if is_rrf:
            field_result = db_con.get_single_coa_data_rrf(coa_id)
        else:
            field_result = db_con.get_single_coa_data(coa_id)

        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50, leftMargin=50, topMargin=90, bottomMargin=30
        )
        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(name="SectionHeader", fontName="Times-Roman", fontSize=14, leading=14, spaceAfter=12, spaceBefore=6, bold=True))
        styles.add(ParagraphStyle(name="SubHeading", fontName="Times-Bold", fontSize=11, leading=14, spaceAfter=4, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="NormalText", fontName="Times-Roman", fontSize=11, leading=12, spaceAfter=4))

        content = []
        page_width = letter[0] - 50 - 50
        content.append(Spacer(1, 70))
        content.append(
            Paragraph(f"Customer: <font name='Times-Bold'>{field_result[1]}</font> ", styles['NormalText']))
        content.append(Spacer(1, 10))  # Small spacer between lines

        content.append(
            Paragraph(f"Color Code: {field_result[2]}", styles['NormalText']))
        content.append(Spacer(1, 10))

        if field_result[16]:
            content.append(
                Paragraph(f"ZP Code: {field_result[16]}", styles['NormalText']))
            content.append(Spacer(1, 10))

        quantity = str(field_result[6]).strip()

        # First, try to replace kg/KG/kg./KG. if present at the end
        filtered_quantity = re.sub(r'(\s*kg\.?$|\s*KG\.?$)', ' Kg.', quantity, flags=re.IGNORECASE)

        # If 'kg' is not present at the end, append " Kg."
        if not re.search(r'(kg\.?$|KG\.?$)', quantity.strip(), re.IGNORECASE):
            filtered_quantity = quantity.strip() + " Kg."

        content.append(
            Paragraph(f"Quantity Delivered: {filtered_quantity}", styles['NormalText'])
        )
        content.append(Spacer(1, 10))

        content.append(Paragraph(
            f"Delivery Date: {field_result[7].strftime('%B %d, %Y')}",
            styles['NormalText']))
        content.append(Spacer(1, 10))

        content.append(
            Paragraph(f"Lot Number: {field_result[3]}", styles['NormalText']))
        content.append(Spacer(1, 10))

        content.append(Paragraph(
            f"Production Date: {field_result[8].strftime('%B %d, %Y')}",
            styles['NormalText']))
        content.append(Spacer(1, 10))

        if field_result[18]:
            content.append(Paragraph(
                f"Expiration Date: {field_result[18].strftime('%B %d, %Y')}",
                styles['NormalText']))
            content.append(Spacer(1, 10))
        if field_result[17]:
            content.append(
                Paragraph(f"Date Evaluated: {field_result[17].strftime('%B %d, %Y')}", styles['NormalText']))
            content.append(Spacer(1, 10))
        if is_rrf:
            delivery_receipt_text = Paragraph(
                f"RRF Number: {field_result[5]}", styles['NormalText'])
        else:
            delivery_receipt_text = Paragraph(
                f"Delivery Receipt Number: {field_result[5]}", styles['NormalText'])
        right_aligned_paragraph_style = ParagraphStyle(
            name="RightAlignedCellText",
            parent=styles['NormalText'],  # Inherit from NormalText for font, size etc.
            alignment=2  # Set the internal alignment of the paragraph
        )
        if field_result[4]:  # not None and not ""
            po_number_text = Paragraph(
                f"P.O Number: {field_result[4]}",
                right_aligned_paragraph_style
            )
        else:
            po_number_text = Paragraph("", right_aligned_paragraph_style)

        # Calculate page width for column widths
        page_width = letter[0] - 50 - 50

        delivery_po_table = Table(
            [[delivery_receipt_text, po_number_text]],
            colWidths=[page_width * 0.5, page_width * 0.5],  # Adjust ratio as desired
            hAlign='LEFT',  # The table itself is left-aligned on the page
            style=[
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Align content of the first column to the left
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),  # Align content of the second column to the right
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertically center content if needed
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 20),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0)
            ]
        )
        content.append(delivery_po_table)

        content.append(Spacer(1, 28))

        content.append(Paragraph("<u><b>Summary of Analysis</b></u>", styles["SubHeading"]))
        content.append(Spacer(1, 12))
        # Summary of Analysis Table
        if is_rrf:
            rows = db_con.get_coa_analysis_results_rrf(coa_id)
        else:
            rows = db_con.get_coa_analysis_results(coa_id)
        summary_data = [["", "Standard", "Delivery"]]
        for row in rows:  # Fixed typo: rows -> row
            parameter = row[0]
            standard_value = row[1]
            delivery_value = row[2]
            summary_data.append([parameter, standard_value, delivery_value])

        page_width, _ = letter  # or: page_width, _ = doc.pagesize if accessible
        printable_width = page_width - 50 - 50  # leftMargin, rightMargin

        summary_table = Table(summary_data, colWidths=[printable_width / 3] * 3, hAlign="LEFT")  # Adjusted colWidths for better match, hAlign LEFT
        summary_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
            ('LINEBELOW', (0, 0), (-1, -1), 0.75, colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align first column
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Center other columns
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Roman'),  # Header row
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),  # Smaller font size to match
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),  # Reduced padding for tighter rows
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(summary_table)
        if "h&e" in field_result[1].lower():
            content.append(Spacer(1, 20))
        else:
            content.append(Spacer(1, 32))

        name_len = len(field_result[10])
        lines = "_" * name_len  # Keep simple underline
        indent = ParagraphStyle(
            name="indent",
            fontName="Times-Roman", fontSize=11, leading=12,  # Inherit from NormalText for font, size etc.
            leftIndent=64
        )
        pos_indent = ParagraphStyle(
            name="indent",
            parent=styles['NormalText'],  # Inherit from NormalText for font, size etc.
            leftIndent=80
        )
        content.append(Paragraph(f"Certified by: {lines}", styles["NormalText"]))
        content.append(Paragraph(str(field_result[10]), indent))
        if "h&e" in field_result[1].lower():
            content.append(Paragraph("QC Analyst", pos_indent))
        content.append(Paragraph("Date: " + str(field_result[9].strftime('%B %d, %Y')), styles["NormalText"]))
        content.append(Spacer(1, 38))  # Reduced spacer before storage

        # Storage section
        # Serif font styles (already Times)
        NormalSerif = ParagraphStyle(
            "NormalSerif",
            fontName="Times-Roman",
            fontSize=9,
            leading=12,
            spaceAfter=10  # Reduced spaceAfter
        )
        BoldSerif = ParagraphStyle(
            "BoldSerif",
            fontName="Times-Roman",
            fontSize=9,  # Smaller to match
            leading=12,
            spaceAfter=0  # Reduced
        )
        content.append(Paragraph("STORAGE", BoldSerif))
        content.append(Paragraph(str(field_result[11]), NormalSerif))

        shelf_life_data = str(field_result[12]).strip()

        if ":" in shelf_life_data:
            before_colon, after_colon = shelf_life_data.split(":", 1)  # split only once
            before_colon = before_colon.strip()
            after_colon = after_colon.strip()

            # Bold line with Shelf Life and value
            content.append(Paragraph(f"Shelf Life: {before_colon}", BoldSerif))
            # Normal line for the description
            if after_colon:
                content.append(Paragraph(after_colon, NormalSerif))
        else:
            # No colon → display whole thing in NormalSerif
            content.append(Paragraph("Shelf Life:", BoldSerif))
            content.append(Paragraph(shelf_life_data, NormalSerif))

        if field_result[13]:
            content.append(Paragraph("Suitability: " + str(field_result[13]), BoldSerif))

        if field_result[15]:
            if "everest plastic" in field_result[1].lower():
                hanging_indent = ParagraphStyle(
                    "HangingIndentNote",
                    parent=BoldSerif,  # Inherit from your BoldSerif style
                    leftIndent=23,  # Indent all lines by 40pt (adjust as needed)
                    firstLineIndent=-23,  # Pull first line left by same amount
                    spaceAfter=10  # Any extra space after the note
                )

                note_content = field_result[15]                # Convert \n to <br/> in ReportLab paragraphs for line breaks
                note_content_html = note_content.replace("\n", "<br/>")
                note_param = Paragraph(f"Note: {note_content_html}", hanging_indent)

                content.append(note_param)
            else:
                content.append(Paragraph(str(field_result[15].replace("\n", "<br/>")), BoldSerif))

        content.append(Spacer(1, 14))  # Space before footer note

        doc.build(content, onFirstPage=add_coa_header)
        buffer.seek(0)
        return buffer.getvalue()  # returns PDF bytes

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