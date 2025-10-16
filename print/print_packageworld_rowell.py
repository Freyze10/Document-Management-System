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
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Indenter

from alert import window_alert
from utils import abs_path
from db import db_con
from print.pdf_header import add_coa_header_only


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
        """Generate PDF from Rowell inspection data (precisely aligned with COI PDF layout)"""
        field_result = db_con.get_single_coa_data(coa_id)
        properties_table_result = db_con.get_packageworld_rowell_properties(coa_id)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=60, leftMargin=60, topMargin=95, bottomMargin=45
        )

        styles = getSampleStyleSheet()

        # === Font hierarchy and custom styles ===
        styles.add(ParagraphStyle(
            name="CustomTitle",
            fontName="Helvetica",
            fontSize=20,
            leading=16,
            alignment=TA_CENTER
        ))

        styles.add(ParagraphStyle(
            name="CustomSubtitle",
            fontName="Times-Roman",
            fontSize=12,
            leading=14,
            alignment=TA_CENTER
        ))

        styles.add(ParagraphStyle(
            name="SectionHeader",
            fontName="Times-Roman",
            fontSize=11,
            leading=14,
            spaceBefore=10,
            spaceAfter=4
        ))

        styles.add(ParagraphStyle(
            name="FieldLabel",
            fontName="Times-Roman",
            fontSize=11,
            leading=13,
            spaceAfter=2
        ))

        styles.add(ParagraphStyle(
            name="TableLabel_left",
            fontName="Times-Roman",
            fontSize=11,
            leading=13,
            # alignment = TA_CENTER
        ))

        styles.add(ParagraphStyle(
            name="TableLabel",
            fontName="Times-Roman",
            fontSize=11,
            leading=13,
            alignment=TA_CENTER
        ))
        styles.add(ParagraphStyle(
            name="TableLabelBold",
            fontName="Times-Roman",
            fontSize=11,
            leading=13,
            alignment=TA_CENTER
        ))
        styles.add(ParagraphStyle(
            name="SmallText",
            fontName="Times-Italic",
            fontSize=9,
            leading=11,
            leftIndent=10,
            spaceAfter=10
        ))

        content = []

        # === HEADER SECTION ===
        content.append(Paragraph("CERTIFICATE OF INSPECTION", styles["CustomTitle"]))
        content.append(Spacer(1, 24))
        content.append(Paragraph("<u>PVC-FREE COMPOUND FOOD APPROVED</u>", styles["CustomSubtitle"]))
        content.append(Spacer(1, 22))

        # === CUSTOMER INFO (table without borders) ===
        page_width = letter[0] - 120
        field_rows = []

        def add_field_row(label, value):
            field_rows.append([
                Paragraph(f"<b>{label}</b>", styles["FieldLabel"]),
                Paragraph(value, styles["FieldLabel"])
            ])

        # 🗓 Manufacturing Date formatting
        mfg_date = field_result[8]
        if isinstance(mfg_date, datetime):
            mfg_date_str = mfg_date.strftime("%B %d, %Y")
        else:
            formatted_dates = []
            for d in str(mfg_date).split(","):
                d = d.strip()
                try:
                    parsed = datetime.strptime(d, "%Y-%m-%d")
                    formatted_dates.append(parsed.strftime("%B %d, %Y"))
                except ValueError:
                    formatted_dates.append(d)
            mfg_date_str = ", ".join(formatted_dates)

        # 🧾 Add field rows
        add_field_row("Customer:", field_result[1])
        add_field_row("Product Name:", properties_table_result[0][0])
        add_field_row("Code:", field_result[2])
        add_field_row("Lot Number:", field_result[3])
        add_field_row("Total Quantity:", field_result[6])
        add_field_row("Manufacturing Date:", mfg_date_str)

        # Shelf Life formatting
        shelf_life_value = str(field_result[12]).strip()
        if "*" in shelf_life_value:
            before_star, after_star = shelf_life_value.split("*", 1)
            combined = (
                f'<font name="Times-Roman" size="11">{before_star.strip()}</font>'
                '<br/>'
                f'<font name="Times-Roman" size="9">*{after_star.strip()}</font>'
            )
            add_field_row("Shelf Life:", combined)
        else:
            add_field_row("Shelf Life:", shelf_life_value)

        info_table = Table(field_rows, colWidths=[page_width * 0.25, page_width * 0.75])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 12))

        # === SECTION HEADER ===
        content.append(Paragraph("<u>PHYSICAL / TYPICAL PROPERTIES</u>", styles["SectionHeader"]))
        content.append(Spacer(1, 12))

        # === TABLE DATA ===
        table_data = []
        header_row = [
            Paragraph("", styles["TableLabelBold"]),
            Paragraph("New Delivery", styles["TableLabelBold"]),
            Paragraph("Standard", styles["TableLabelBold"]),
            Paragraph("Method Used", styles["TableLabelBold"])
        ]
        table_data.append(header_row)

        # Assume: rows for Pellet Size Length, mm and Diameter, mm are consecutive
        combined_label = None
        combined_value = []
        combined_std = []
        combined_method = []

        for i, row in enumerate(properties_table_result[1:]):
            label_text = row[0]
            if label_text.strip() == "Pellet Size Length, mm":
                # Start combining
                combined_label = "Pellet Size<br/>Length, mm"
                combined_value = [str(row[1])]
                combined_std = [str(row[2])]
                combined_method = [str(row[3])]
                # Look ahead for "Diameter, mm"
                if i + 2 <= len(properties_table_result[1:]):
                    next_row = properties_table_result[1:][i + 1]
                    if next_row[0].strip() == "Diameter, mm":
                        combined_label += "<br/>Diameter, mm"
                        combined_value.append(str(next_row[1]))
                        combined_std.append(str(next_row[2]))
                        skip_next = True
                    else:
                        skip_next = False
                else:
                    skip_next = False

                label_p = Paragraph(combined_label, styles["TableLabel_left"])
                value_p = Paragraph("<br/>".join(combined_value), styles["TableLabel"])
                std_p = Paragraph("<br/>".join(combined_std), styles["TableLabel"])
                method_p = Paragraph("<br/>".join(combined_method), styles["TableLabel"])
                table_data.append([label_p, value_p, std_p, method_p])
            elif label_text.strip() == "Diameter, mm" and 'skip_next' in locals() and skip_next:
                skip_next = False  # Already processed above, skip this time
                continue
            else:
                label_p = Paragraph(label_text, styles["TableLabel_left"])
                value_p = Paragraph(str(row[1]), styles["TableLabel"])
                std_p = Paragraph(str(row[2]), styles["TableLabel"])
                method_p = Paragraph(str(row[3]), styles["TableLabel"])
                table_data.append([label_p, value_p, std_p, method_p])

        properties_table = Table(
            table_data,
            colWidths=[page_width * 0.25, page_width * 0.25, page_width * 0.25, page_width * 0.25]
        )

        table_style = [
            ('ALIGN', (0, 0), (3, -1), 'CENTER'),  # Center header row
            ('GRID', (0, 0), (-1, -1), 0.75, colors.black),

            # Vertical alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('VALIGN', (1, 4), (2, 4), 'BOTTOM'),
            ('VALIGN', (1, 4), (2, 4), 'BOTTOM'),

            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),

            # Font setup
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
        ]

        properties_table.setStyle(TableStyle(table_style))
        content.append(properties_table)
        content.append(Spacer(1, 25))

        # === CERTIFICATION SECTION ===
        cert_date = field_result[9]
        cert_date_str = cert_date.strftime("%B %d, %Y") if isinstance(cert_date, datetime) else cert_date

        font_name = styles["FieldLabel"].fontName
        font_size = styles["FieldLabel"].fontSize
        content.append(Paragraph("Certified by:  ________________________", styles["FieldLabel"]))
        underline_text = "________________________"
        underline_width = stringWidth(underline_text, font_name, font_size)
        name_width = stringWidth(str(field_result[10]), font_name, font_size)
        cert_label_width = stringWidth("Certified by:  ", font_name, font_size)
        indent_value = cert_label_width + (underline_width - name_width) / 2

        indent_style = ParagraphStyle(name="Indented", parent=styles["FieldLabel"], leftIndent=indent_value)
        content.append(Paragraph(field_result[10], indent_style))

        position_width = stringWidth(str(properties_table_result[0][1]), font_name, font_size)
        indent_value_plus = cert_label_width + (underline_width - position_width) / 2
        indent_style_plus = ParagraphStyle(name="Indented", parent=styles["FieldLabel"], leftIndent=indent_value_plus)
        content.append(Paragraph(properties_table_result[0][1], indent_style_plus))
        content.append(Paragraph(f"Date: {cert_date_str}", styles["FieldLabel"]))

        doc.build(content, onFirstPage=add_coa_header_only)
        buffer.seek(0)
        return buffer.getvalue()

    def show_pdf_preview(self, coa_id, filename):
        self.file_name = filename
        self.coa_id = coa_id
        pdf_bytes = self.generate_pdf(coa_id)
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
