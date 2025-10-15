import re

from PyQt6.QtCore import QDate, Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QLabel, QHBoxLayout, QHeaderView, QTableWidgetItem, QLineEdit,
    QAbstractItemView, QWidget, QVBoxLayout, QGroupBox, QGridLayout,
    QTableWidget, QScrollArea, QDateEdit, QPushButton
)

from db import db_dr, db_con
from utils import abs_path, lot_format, multiple_dates  # Assuming utils is available with abs_path
from utils.loading import LoadingDialog
from utils.debounce import setup_finished_typing

class RowellWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.default_values()
    def setup_ui(self):
        # Main container with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # Create the form widget that will be inside scroll area
        form_widget = QWidget()
        main_v_layout = QVBoxLayout(form_widget)
        main_v_layout.setContentsMargins(30, 20, 30, 30)

        calendar_icon_path = abs_path.resource("img/calendar_icon.png").replace("\\", "/")

        form_widget.setStyleSheet(f"""
            QWidget {{
                background-color: #f8f9fa;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                color: #343a40;
            }}
            QLabel {{
                font-size: 14px;
                font-weight: 500;
                color: #495057;
                padding-bottom: 2px;
                background-color: transparent;
            }}
            QLabel[class="section_title"] {{
                font-size: 18px;
                font-weight: 600;
                color: #212529;
                margin-top: 10px;
                margin-bottom: 16px;
                padding-bottom: 5px;
                text-align: center; 
            }}
            QLineEdit, QDateEdit {{
                font-size: 12px;
                padding: 6px 8px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: #ffffff;
                min-height: 28px;
                min-width: 80px;
                selection-background-color: #aed6f1;
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border: 1px solid #007bff;
                background-color: #e9f5ff;
            }}
            QDateEdit::drop-down {{
                border: 0px;
                width: 40px;
                background-color: #e9ecef;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QDateEdit::down-arrow {{
                background-image: url("{calendar_icon_path}");
                width: 26px;
                height: 26px;
            }}
            QDateEdit::drop-down:hover {{
                background-color: #dee2e6;
            }}
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: #212529;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 2.0ex;
                background-color: #ffffff;
                padding: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 15px;
                margin-left: 0px;
                color: #34495e;
                background-color: #f8f9fa;
            }}
            QPushButton {{
                background-color: #007bff;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 6px 12px;
                border: none;
                border-radius: 6px;
                min-width: 90px;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: #0056b3;
            }}
            QPushButton:pressed {{
                background-color: #004085;
            }}
        """)

        # === Header ===
        header = QLabel("Certificate of Inspection\nPVC-FREE COMPOUND FOOD APPROVED")
        header.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 30px;
            padding-bottom: 10px;
            border-bottom: 3px solid #007bff;
            text-align: center;
        """)
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(header)
        header_layout.addStretch()
        main_v_layout.addLayout(header_layout)

        # === Section 1: General Info ===
        general_info_group = QGroupBox()
        general_info_layout = QGridLayout()
        general_info_group.setLayout(general_info_layout)

        general_info_layout.setHorizontalSpacing(30)
        general_info_layout.setVerticalSpacing(15)
        general_info_layout.setContentsMargins(20, 25, 20, 20)

        # Initialize input fields
        self.customer_input = QLineEdit()
        self.product_name_input = QLineEdit()
        self.code_input = QLineEdit()
        self.lot_number_input = QLineEdit()
        self.quantity_input = QLineEdit()
        self.manufacturing_date_input = multiple_dates.MultiDateInput()
        self.shelf_life_input = QLineEdit()
        self.delivery_receipt_input = QLineEdit()
        self.delivery_receipt_timer = setup_finished_typing(
            self,
            self.delivery_receipt_input,
            lambda: self.populate_data(self.delivery_receipt_input.text()),
            delay=1200
        )
        # Initialize certification fields
        self.certified_by_name_input = QLineEdit()
        self.position_input = QLineEdit()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())

        # Row 0
        general_info_layout.addWidget(QLabel("Customer:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.customer_input, 0, 1)
        general_info_layout.addWidget(QLabel("Product Name:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.product_name_input, 0, 3)

        # Row 1
        general_info_layout.addWidget(QLabel("Code:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.code_input, 1, 1)
        general_info_layout.addWidget(QLabel("Lot Number:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.lot_number_input, 1, 3)

        # Row 2: Delivery Receipt with Sync Button
        general_info_layout.addWidget(QLabel("Delivery Receipt:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        receipt_input_layout = QHBoxLayout()
        receipt_input_layout.addWidget(self.delivery_receipt_input, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.sync_button = QPushButton("Sync")
        sync_style = """
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 13px;
                font-weight: 500;
                padding: 6px 8px;
                border: none;
                border-radius: 6px;
                min-width: 50px;
                max-width: 65px;
                min-height: 28px;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:pressed { background-color: #1e7e34; }
        """
        self.sync_button.setStyleSheet(sync_style)
        self.sync_button.clicked.connect(self.run_sync_script)
        receipt_input_layout.addWidget(self.sync_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        general_info_layout.addLayout(receipt_input_layout, 2, 1)

        general_info_layout.addWidget(QLabel("Total Quantity:"), 2, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.quantity_input, 2, 3)

        # Row 3
        general_info_layout.addWidget(QLabel("Manufacturing Date:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.manufacturing_date_input, 3, 1)
        general_info_layout.addWidget(QLabel("Shelf Life:"), 3, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.shelf_life_input, 3, 3)

        main_v_layout.addWidget(general_info_group)

        # === Section 2: Physical / Typical Properties ===
        properties_group = QGroupBox("Physical / Typical Properties")
        properties_layout = QVBoxLayout()
        properties_group.setLayout(properties_layout)
        properties_layout.setContentsMargins(20, 25, 20, 20)

        self.properties_table = self.create_properties_table()
        table_container = QHBoxLayout()
        table_container.addStretch()
        table_container.addWidget(self.properties_table)
        table_container.addStretch()
        properties_layout.addLayout(table_container)

        main_v_layout.addWidget(properties_group)

        # === Section 3: Certification ===
        certification_group = QGroupBox()
        certification_layout = QGridLayout()
        certification_group.setLayout(certification_layout)
        certification_layout.setHorizontalSpacing(30)
        certification_layout.setVerticalSpacing(15)
        certification_layout.setContentsMargins(20, 25, 20, 20)

        # Certified by name
        certification_layout.addWidget(QLabel("Certified by:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.certified_by_name_input, 0, 1)

        # Date
        certification_layout.addWidget(QLabel("Date:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.date_input, 0, 3)

        # Position
        certification_layout.addWidget(QLabel("Position:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.position_input, 1, 1, 1, 1)

        main_v_layout.addWidget(certification_group)

        # === Submit Button ===
        submit_button_row = QHBoxLayout()
        submit_button_row.addStretch()

        self.btn_submit = QPushButton("Submit")
        self.btn_submit.clicked.connect(self.on_submit_clicked)
        submit_button_row.addWidget(self.btn_submit)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        self.btn_clear.clicked.connect(self.clear_form)
        submit_button_row.addWidget(self.btn_clear)

        submit_button_row.addStretch()
        main_v_layout.addLayout(submit_button_row)

        main_v_layout.addStretch(1)

        # Set the form widget to scroll area
        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area)

    def create_properties_table(self):
        table = self.setup_table_widget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Property", "New Delivery", "Standard", "Method Used"])
        return table

    def setup_table_widget(self):
        table = QTableWidget()
        table.setMinimumWidth(1250)
        table.setMaximumWidth(1350)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                gridline-color: #f0f2f5;
                alternate-background-color: #fcfcfc;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f8f9fa;
            }
            QTableWidget::item:selected {
                background-color: #e0f2fe;
                color: #212529;
            }
            QTableWidget::item:hover {
                background-color: #f1f8ff;
            }
            QHeaderView::section {
                font-size: 14px;
                font-weight: 600;
                padding: 10px;
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #495057;
            }
            QHeaderView::section:horizontal {
                border-bottom: 2px solid #007bff;
            }
            QTableCornerButton::section {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-top-left-radius: 8px;
            }
            QTableWidget QScrollBar:vertical {
                border: none;
                background: #f1f3f5;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QTableWidget QScrollBar::handle:vertical {
                background: #adb5bd;
                border-radius: 6px;
                min-height: 20px;
            }
            QTableWidget QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        return table

    def adjust_table_height(self):
        fixed_row_height = 48
        for i in range(self.properties_table.rowCount()):
            self.properties_table.setRowHeight(i, fixed_row_height)
        row_height_total = self.properties_table.rowCount() * fixed_row_height
        header_height = self.properties_table.horizontalHeader().height()
        table_border_thickness = 2
        self.properties_table.setFixedHeight(row_height_total + header_height + table_border_thickness + 4)

    def default_values(self):
        self.customer_input.setText("Rowell Lithography & Metal Closure, Inc.")
        self.product_name_input.setText("Riteseal 88 Non PVC Liner Compound Blue")
        self.shelf_life_input.setText(
            "12 months from date of production *Shelf life is stated as a maximum from date of production when the product is stored in unbroken packaging.")
        self.certified_by_name_input.setText("Linzy Jam Bautista")
        self.position_input.setText("QC Analyst")

        properties_data = [
            ("Color", "Blue", "Blue", "MBPI"),
            ("Specific Gravity", "1.00", "1.00 ± 0.20", "MBPI"),
            ("Durometer Hardness Shore \"A\"", "88.02", "90.0 ± 5.00", "ASTM D 2240"),
            ("Pellet Size Length, mm", "3.00", "3.00 ± 0.50", "MBPI"),
            ("Diameter, mm", "2.90", "2.50 ± 0.50", "MBPI"),
            ("Odor", "no undesirable odor", "no undesirable odor", "MBPI")
        ]

        self.properties_table.setRowCount(len(properties_data))
        for row_idx, (property_name, delivery, standard, method) in enumerate(properties_data):
            self.properties_table.setItem(row_idx, 0, QTableWidgetItem(property_name))
            self.properties_table.setItem(row_idx, 1, QTableWidgetItem(delivery))
            self.properties_table.setItem(row_idx, 2, QTableWidgetItem(standard))
            self.properties_table.setItem(row_idx, 3, QTableWidgetItem(method))

        self.adjust_table_height()

    def populate_data(self, dr_no):
        records = db_con.get_dr_details(dr_no)

        if not records:
            # No data, clear fields
            self.default_values()
            self.code_input.clear()
            self.lot_number_input.clear()
            self.quantity_input.clear()
            self.manufacturing_date_input.clear_value()
            return

        # Find the first record that is NOT yet in your database
        selected_record = None
        for record in records:
            dr_no_val = record[0]
            product_code_val = record[1]
            if not db_con.record_exists(dr_no_val, product_code_val):
                selected_record = record
                break

        # If all records exist, fall back to first one
        if selected_record is None:
            selected_record = records[0]

        lot_no = lot_format.normalize(selected_record[5])

        self.customer_input.setText(str(selected_record[2]))
        self.code_input.setText(str(selected_record[1]))
        self.lot_number_input.setText(lot_no)
        self.quantity_input.setText(str(selected_record[6]))

    def get_properties_table_data(self):
        data = {}
        row_count = self.properties_table.rowCount()
        col_count = self.properties_table.columnCount()

        for row in range(row_count):
            # Get values in that row
            row_values = []
            for col in range(col_count):
                cell_item = self.properties_table.item(row, col)
                value = cell_item.text() if cell_item else ""
                row_values.append(value)

            # Store row header with its values
            data[row] = row_values

        return data
    
    def clear_form(self):
        """Clear all input fields"""
        self.default_values()
        self.code_input.clear()
        self.lot_number_input.clear()
        self.quantity_input.clear()
        self.manufacturing_date_input.clear_value()

    def on_submit_clicked(self):
        """Handle submit button click"""
        # Collect data from fields
        data = {
            'customer': self.customer_input.text(),
            'product_name': self.product_name_input.text(),
            'code': self.code_input.text(),
            'lot_number': self.lot_number_input.text(),
            'quantity': self.quantity_input.text(),
            'manufacturing_date': self.manufacturing_date_input.get_selected_dates(),
            'shelf_life': self.shelf_life_input.text(),
            'certified_by': self.certified_by_name_input.text(),
            'position': self.position_input.text(),
            'date': self.date_input.date().toString("yyyy-MM-dd")
        }
        properties_data = self.get_properties_table_data()
        # Process the data (you can implement your own logic here)
        print("Form submitted with data:", data)
        print("Form table with data:", properties_data)

        # Optionally, you can add database operations here
        # db_con.insert_rowell_data(data)

    def run_sync_script(self):
        # Show loading dialog
        self.loading = LoadingDialog(self)
        self.loading.show()

        # Run in a worker thread instead of subprocess
        class Worker(QThread):
            finished = pyqtSignal()

            def run(self):
                db_dr.SyncDeliveryWorker().run()  # or whatever function starts sync
                self.finished.emit()

        self.worker = Worker()
        self.worker.finished.connect(self.loading.accept)
        self.worker.start()