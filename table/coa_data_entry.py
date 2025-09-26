import re
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QLabel, QHBoxLayout, QHeaderView, QPushButton, QTableWidgetItem,
    QAbstractItemView, QWidget, QVBoxLayout, QGroupBox, QGridLayout, QTableWidget, QLineEdit
)
from db import db_con
from utils import abs_path, lot_format

current_coa_id = None
dr_num = ""

def load_coa_details(self, coa_id, is_rrf):
    self.color_code_input.blockSignals(True)
    self.delivery_receipt_input.blockSignals(True)
    if is_rrf:
        field_result = db_con.get_single_coa_data_rrf(coa_id)
        analysis_table_result = db_con.get_coa_analysis_results_rrf(coa_id)
    else:
        field_result = db_con.get_single_coa_data(coa_id)
        analysis_table_result = db_con.get_coa_analysis_results(coa_id)

    # Populate inputs
    self.coa_customer_input.setText(str(field_result[1]))
    self.color_code_input.setText(str(field_result[2]))
    self.lot_number_input.setText(str(field_result[3]))
    self.po_number_input.setText(str(field_result[4]))
    self.delivery_receipt_input.setText(str(field_result[5]))
    self.quantity_delivered_input.setText(str(field_result[6]))

    # Handle potential None for dates
    if field_result[7]:
        self.delivery_date_input.setDate(QDate(field_result[7].year, field_result[7].month, field_result[7].day))
    if field_result[8]:
        self.production_date_input.setDate(QDate(field_result[8].year, field_result[8].month, field_result[8].day))
    if field_result[9]:
        self.creation_date_input.setDate(QDate(field_result[9].year, field_result[9].month, field_result[9].day))

    self.certified_by_input.setText(str(field_result[10]))
    self.coa_storage_input.setText(str(field_result[11]))
    self.coa_shelf_life_input.setText(str(field_result[12]))
    self.suitability_input.setText(str(field_result[13]))
    self.btn_coa_submit.setText("Update")

    # Populate table
    self.summary_analysis_table.clearContents()
    self.summary_analysis_table.setRowCount(len(analysis_table_result))
    self.summary_analysis_table.setColumnCount(2)
    self.summary_analysis_table.setHorizontalHeaderLabels(["Standard Value", "Delivery Value"])

    for row_idx, (parameter_name, standard_value, delivery_value) in enumerate(analysis_table_result):
        self.summary_analysis_table.setVerticalHeaderItem(row_idx, QTableWidgetItem(parameter_name))
        self.summary_analysis_table.setItem(row_idx, 0, QTableWidgetItem(str(standard_value) if standard_value else ""))
        self.summary_analysis_table.setItem(row_idx, 1, QTableWidgetItem(str(delivery_value) if delivery_value else ""))

    adjust_table_height(self)

    self.color_code_input.blockSignals(False)
    self.delivery_receipt_input.blockSignals(False)

def coa_data_entry_form(self, is_rrf=False):
    try:
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
<<<<<<< HEAD
                font-size: 14px;
                padding: 10px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: #ffffff;
                min-height: 38px;
=======
                font-size: 12px;
                padding: 6px 8px;
                border: 1px solid #ced4da; /* Lighter, more neutral border */
                border-radius: 6px; /* Slightly less rounded for a crisp look */
                background-color: #ffffff;
                min-height: 28px; /* Consistent height */
>>>>>>> main
                selection-background-color: #aed6f1;
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border: 1px solid #007bff;
                background-color: #e9f5ff;
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
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
            QDateEdit::down-arrow:on {{
                top: 1px;
                left: 1px;
            }}
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: #212529;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 2.0ex;
                background-color: #ffffff;
<<<<<<< HEAD
                padding: 15px;
=======
                padding: 10px; /* Inner padding for group box content */
>>>>>>> main
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
        """)

        # Header
        header = self.coa_header_label
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

        # Section 1: General Info
        general_info_group = QGroupBox()
        general_info_layout = QGridLayout()
        general_info_group.setLayout(general_info_layout)

        general_info_layout.setHorizontalSpacing(30)
        general_info_layout.setVerticalSpacing(15)
        general_info_layout.setContentsMargins(20, 25, 20, 20)

        # Row 0
        general_info_layout.addWidget(QLabel("Customer:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.coa_customer_input, 0, 1)
        general_info_layout.addWidget(QLabel("Color Code:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.color_code_input, 0, 3)

        # Row 1
        general_info_layout.addWidget(QLabel("Lot Number:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.lot_number_input, 1, 1)
        general_info_layout.addWidget(QLabel("Quantity Delivered:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.quantity_delivered_input, 1, 3)

        # Row 2: Delivery Receipt & PO Number
        general_info_layout.addWidget(self.delivery_receipt_label, 2, 0, Qt.AlignmentFlag.AlignRight)
        receipt_input_layout = QHBoxLayout()
        receipt_input_layout.addWidget(self.delivery_receipt_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.sync_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 13px;
                font-weight: 500;
<<<<<<< HEAD
                padding: 7px 10px;
                border: none;
                border-radius: 6px;
                min-width: 60px;
                max-width: 75px;
                min-height: 36px;
=======
                padding: 6px 8px; /* Adjusted padding */
                border: none;
                border-radius: 6px;
                min-width: 50px; /* Adjusted min-width */
                max-width: 65px; /* Adjusted max-width */
                min-height: 28px; /* Slightly smaller height */
>>>>>>> main
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:pressed { background-color: #1e7e34; }
        """)
        receipt_input_layout.addWidget(self.sync_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        general_info_layout.addLayout(receipt_input_layout, 2, 1)

        general_info_layout.addWidget(QLabel("P.O Number:"), 2, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.po_number_input, 2, 3)

        # Row 3: Dates
        general_info_layout.addWidget(QLabel("Delivery Date:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.delivery_date_input, 3, 1)
        general_info_layout.addWidget(QLabel("Production Date:"), 3, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.production_date_input, 3, 3)

        main_v_layout.addWidget(general_info_group)

        # Section 2: Summary of Analysis
        summary_analysis_group = QGroupBox()
        summary_analysis_layout = QVBoxLayout()
        summary_analysis_group.setLayout(summary_analysis_layout)
        summary_analysis_layout.setContentsMargins(20, 25, 20, 20)

        section2_header = QLabel("Summary of Analysis")
        section2_header.setProperty("class", "section_title")

        self.summary_analysis_table.setColumnCount(2)
        self.summary_analysis_table.setRowCount(3)
        self.summary_analysis_table.setHorizontalHeaderLabels(["Standard", "Delivery"])
        self.summary_analysis_table.setVerticalHeaderLabels([
            "Color", "Light Fastness (1-8)", "Heat Stability (1-5)"
        ])
        self.summary_analysis_table.setMinimumWidth(650)
        self.summary_analysis_table.setMaximumWidth(850)
        self.summary_analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.summary_analysis_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.summary_analysis_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.summary_analysis_table.setStyleSheet("""
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
        self.summary_analysis_table.setAlternatingRowColors(True)
        adjust_table_height(self)

        sub_header_cont = QHBoxLayout()
        sub_header_cont.addStretch()
        sub_header_cont.addWidget(section2_header)
        sub_header_cont.addStretch()
        table_container = QHBoxLayout()
        table_container.addStretch()
        table_container.addWidget(self.summary_analysis_table)
        table_container.addStretch()

        summary_analysis_layout.addLayout(sub_header_cont)
        summary_analysis_layout.addLayout(table_container)

        # Buttons for table
        btn_add_row = QPushButton("Add Row")
        btn_add_row.clicked.connect(self.add_row_to_coa_summary_table)
        btn_delete_row = QPushButton("Delete Row")
        btn_delete_row.clicked.connect(self.delete_row_from_coa_summary_table)
        btn_delete_row.setProperty("class", "delete")

        button_style = """
            QPushButton {
                background-color: #28a745;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
<<<<<<< HEAD
                padding: 6px 16px;
                border: none;
                border-radius: 6px;
                min-width: 100px;
                min-height: 38px;
=======
                padding: 6px 12px; /* Adjusted padding */
                border: none;
                border-radius: 6px;
                min-width: 80px; /* Adjusted min-width */
                min-height: 30px; /* Adjusted min-height */
>>>>>>> main
                transition: background-color 0.2s ease, box-shadow 0.2s ease;
            }
            QPushButton:hover {
                background-color: #218838;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton[class="delete"] {
                background-color: #dc3545;
            }
            QPushButton[class="delete"]:hover {
                background-color: #c82333;
            }
            QPushButton[class="delete"]:pressed {
                background-color: #bd2130;
            }
            QPushButton:focus {
                outline: none;
                border: 2px solid #007bff;
            }
        """

        btn_add_row.setStyleSheet(button_style)
        btn_delete_row.setStyleSheet(button_style)

        # Adjust submit button specifically
        submit_button_style = button_style.replace("#28a745", "#007bff")
        submit_button_style = submit_button_style.replace("#218838", "#0056b3")
        submit_button_style = submit_button_style.replace("#1e7e34", "#004085")
        submit_button_style = submit_button_style.replace("min-width: 100px;", "min-width: 120px;")
        submit_button_style = submit_button_style.replace("min-height: 38px;", "min-height: 40px;")
        submit_button_style = submit_button_style.replace("font-size: 14px;", "font-size: 15px;")
        self.btn_coa_submit.setStyleSheet(submit_button_style)

        btn_add_table_row = QHBoxLayout()
        btn_add_table_row.addStretch()
        btn_add_table_row.addWidget(btn_add_row)
        btn_add_table_row.addSpacing(10)
        btn_add_table_row.addWidget(btn_delete_row)
        btn_add_table_row.addStretch()
        summary_analysis_layout.addLayout(btn_add_table_row)

        main_v_layout.addWidget(summary_analysis_group)

        # Section 3: Certification & Other Info
        certification_group = QGroupBox()
        certification_layout = QGridLayout()
        certification_group.setLayout(certification_layout)
        certification_layout.setHorizontalSpacing(30)
        certification_layout.setVerticalSpacing(15)
        certification_layout.setContentsMargins(20, 25, 20, 20)

        # Certified by and Creation Date
        certification_layout.addWidget(QLabel("Certified by:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.certified_by_input, 0, 1)
        certification_layout.addWidget(QLabel("Date:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.creation_date_input, 0, 3)

        # Storage and Suitability
        certification_layout.addWidget(QLabel("Storage:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.coa_storage_input, 1, 1)
        certification_layout.addWidget(QLabel("Suitability:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.suitability_input, 1, 3)

        # Shelf Life
        certification_layout.addWidget(QLabel("Shelf Life:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.coa_shelf_life_input, 2, 1, 1, 3)

        main_v_layout.addWidget(certification_group)

        # Submit Button
        submit_button_row = QHBoxLayout()
        submit_button_row.addStretch()
        submit_button_row.addWidget(self.btn_coa_submit)
        submit_button_row.addStretch()
        main_v_layout.addLayout(submit_button_row)

        main_v_layout.addStretch(1)

        self.coa_form_layout.addWidget(form_widget)
        clear_coa_form(self)
    except Exception as e:
        print(f"Error loading COA form: {e}")

def terumo_data_entry_form(self):
    try:
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
            QLineEdit, QDateEdit, QTextEdit {{
                font-size: 14px;
                padding: 10px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: #ffffff;
                min-height: 38px;
                selection-background-color: #aed6f1;
            }}
            QLineEdit:focus, QDateEdit:focus, QTextEdit:focus {{
                border: 1px solid #007bff;
                background-color: #e9f5ff;
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
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
            QDateEdit::down-arrow:on {{
                top: 1px;
                left: 1px;
            }}
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: #212529;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 2.0ex;
                background-color: #ffffff;
                padding: 15px;
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
            QTableWidget {{
                font-size: 14px;
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                gridline-color: #f0f2f5;
                alternate-background-color: #fcfcfc;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid #f8f9fa;
            }}
            QTableWidget::item:selected {{
                background-color: #e0f2fe;
                color: #212529;
            }}
            QTableWidget::item:hover {{
                background-color: #f1f8ff;
            }}
            QHeaderView::section {{
                font-size: 14px;
                font-weight: 600;
                padding: 10px;
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #495057;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid #007bff;
            }}
            QTableCornerButton::section {{
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-top-left-radius: 8px;
            }}
            QTableWidget QScrollBar:vertical {{
                border: none;
                background: #f1f3f5;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }}
            QTableWidget QScrollBar::handle:vertical {{
                background: #adb5bd;
                border-radius: 6px;
                min-height: 20px;
            }}
            QTableWidget QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        # Header
        header = QLabel("Certificate of Analysis")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 2px solid #007bff;
            text-align: center;
        """)
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(header)
        header_layout.addStretch()
        main_v_layout.addLayout(header_layout)

        # Top Information (Delivery Date, Lot No.)
        top_info_layout = QGridLayout()
        top_info_layout.setHorizontalSpacing(10)
        top_info_layout.setVerticalSpacing(5)

        delivery_date_label = QLabel("Delivery Date:")
        delivery_date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_info_layout.addWidget(delivery_date_label, 0, 2)
        # Assuming self.terumo_delivery_date is a QDateEdit
        self.terumo_delivery_date.setDate(QDate.fromString("May 24, 2024", "MMMM dd, yyyy"))
        top_info_layout.addWidget(self.terumo_delivery_date, 0, 3)

        lot_number_label = QLabel("Lot No.:")
        lot_number_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_info_layout.addWidget(lot_number_label, 1, 2)
        # Assuming self.terumo_lot_number is a QLineEdit
        self.terumo_lot_number.setText("240510 (MB-24-5826AK)")
        top_info_layout.addWidget(self.terumo_lot_number, 1, 3)

        top_info_layout.setColumnStretch(0, 1)
        top_info_layout.setColumnStretch(1, 1)
        top_info_layout.setColumnStretch(2, 1)
        top_info_layout.setColumnStretch(3, 1)

        main_v_layout.addLayout(top_info_layout)

        # Section 1: General Info
        general_info_group = QGroupBox()
        general_info_layout = QGridLayout()
        general_info_group.setLayout(general_info_layout)
        general_info_layout.setHorizontalSpacing(20)
        general_info_layout.setVerticalSpacing(8)
        general_info_layout.setContentsMargins(10, 15, 10, 10)

        general_info_layout.addWidget(QLabel("Customer Name:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        # Assuming self.terumo_customer_input is a QLineEdit
        self.terumo_customer_input.setText("Terumo (Philippines Corporation)")
        general_info_layout.addWidget(self.terumo_customer_input, 0, 1)

        general_info_layout.addWidget(QLabel("Item Code:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        # Assuming self.terumo_item_code is a QLineEdit
        self.terumo_item_code.setText("PL00X800MB")
        general_info_layout.addWidget(self.terumo_item_code, 1, 1)
        general_info_layout.addWidget(QLabel("Quantity:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        # Assuming self.terumo_quantity is a QLineEdit
        self.terumo_quantity.setText("100kg.")
        general_info_layout.addWidget(self.terumo_quantity, 1, 3)

        general_info_layout.addWidget(QLabel("Item Description:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        # Assuming self.terumo_item_desc is a QLineEdit
        self.terumo_item_desc.setText("Masterbatch White WA14429E")
        general_info_layout.addWidget(self.terumo_item_desc, 2, 1, 1, 3)

        main_v_layout.addWidget(general_info_group)

        # Section 2: Molded Chip Inspection
        molded_group = QGroupBox("Molded Chip Inspection")
        molded_layout = QVBoxLayout()
        molded_group.setLayout(molded_layout)
        molded_layout.setContentsMargins(10, 15, 10, 10)

        molded_table = QTableWidget()
        molded_table.setRowCount(4) # Color, Foreign Material Contamination Diameter, Area, Count
        molded_table.setColumnCount(6)
        molded_table.setHorizontalHeaderLabels(["Check items", "Standard (Diameter)", "Standard (Area)", "Standard (Count)", "Actual", "Judgement"])
        molded_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        molded_table.verticalHeader().setVisible(False)
        molded_table.setAlternatingRowColors(True)

        # Row 0: Color
        molded_table.setItem(0, 0, QTableWidgetItem("Color"))
        self.molded_color_standard = QLineEdit("TPC approved standard")
        molded_table.setCellWidget(0, 1, self.molded_color_standard)
        molded_table.setSpan(0, 1, 1, 3) # Span across Standard (Diameter, Area, Count)
        self.molded_color_actual = QLineEdit("Same as standard")
        molded_table.setCellWidget(0, 4, self.molded_color_actual)
        self.molded_color_judgement = QLineEdit("Passed")
        molded_table.setCellWidget(0, 5, self.molded_color_judgement)

        # Row 1: Foreign Material Contamination - Diameter
        molded_table.setItem(1, 0, QTableWidgetItem("Foreign Material Contamination\n  Diameter (mm)"))

        self.molded_fmc_judgement = QLineEdit("Passed")
        molded_table.setCellWidget(2, 5, self.molded_fmc_judgement)
        molded_table.setSpan(2, 5, 2, 1) # Judgement spans 3 rows for FMC

        # Row 2: Foreign Material Contamination - Area
        self.molded_fmc_diameter_standard = QLineEdit("> 0.10 - 0.35")
        molded_table.setCellWidget(2, 1, self.molded_fmc_diameter_standard)
        self.molded_fmc_area_standard = QLineEdit("> 0.01 - 0.10")
        molded_table.setCellWidget(2, 2, self.molded_fmc_area_standard)
        self.molded_fmc_area_count = QLineEdit("6 pcs")
        molded_table.setCellWidget(2, 3, self.molded_fmc_area_count)
        self.molded_fmc_area_actual = QLineEdit("0")
        molded_table.setCellWidget(2, 4, self.molded_fmc_area_actual)

        # Row 3: Foreign Material Contamination - Count (This combines the < 0.10 for diameter and area
        # Using a QLineEdit for the Standard Diameter < 0.10 part
        self.molded_fmc_diameter_standard_less = QLineEdit("< 0.10")
        molded_table.setCellWidget(3, 1, self.molded_fmc_diameter_standard_less)
        # Using a QLineEdit for the Standard Area < 0.10 part
        self.molded_fmc_area_standard_less = QLineEdit("< 0.10")
        molded_table.setCellWidget(3, 2, self.molded_fmc_area_standard_less)
        # Using a QLineEdit for the Standard Count for < 0.10
        self.molded_fmc_count_less = QLineEdit("0 pcs") # Assuming the PDF's '0' is count for <0.10
        molded_table.setCellWidget(3, 3, self.molded_fmc_count_less)
        # Using a QLineEdit for the Actual for < 0.10
        self.molded_fmc_actual_less = QLineEdit("0")
        molded_table.setCellWidget(3, 4, self.molded_fmc_actual_less)


        # Adjust row heights for multi-line text (e.g., Foreign Material Contamination)
        molded_table.resizeRowToContents(1)


        molded_layout.addWidget(molded_table)
        main_v_layout.addWidget(molded_group)

        # Section 3: Pellet Inspection
        pellet_group = QGroupBox("Pellet Inspection")
        pellet_layout = QVBoxLayout()
        pellet_group.setLayout(pellet_layout)
        pellet_layout.setContentsMargins(10, 15, 10, 10)

        # Appearance
        pellet_layout.addWidget(QLabel("Appearance: Free from foreign material. No stickiness of pellets"))
        appearance_table = QTableWidget()
        appearance_table.setRowCount(1)
        appearance_table.setColumnCount(4)
        appearance_table.setHorizontalHeaderLabels(["Start", "Middle", "End", "Judgement"])
        appearance_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        appearance_table.verticalHeader().setVisible(False)
        appearance_table.setAlternatingRowColors(True)

        self.pellet_appearance_start = QLineEdit("0")
        appearance_table.setCellWidget(0, 0, self.pellet_appearance_start)
        self.pellet_appearance_middle = QLineEdit("0")
        appearance_table.setCellWidget(0, 1, self.pellet_appearance_middle)
        self.pellet_appearance_end = QLineEdit("0")
        appearance_table.setCellWidget(0, 2, self.pellet_appearance_end)
        self.pellet_appearance_judgement = QLineEdit("Passed")
        appearance_table.setCellWidget(0, 3, self.pellet_appearance_judgement)
        pellet_layout.addWidget(appearance_table)

        # Dimension
        pellet_layout.addWidget(QLabel("Dimension: 3 x 3 ± 0.5 mm pellet diameter and length"))
        pellet_layout.addWidget(QLabel(
            "Single cut, partially cut or double pellet shall be treated as single pellet and must be within the set acceptance criteria"))
        dimension_table = QTableWidget()
        dimension_table.setRowCount(1)
        dimension_table.setColumnCount(4)
        dimension_table.setHorizontalHeaderLabels(["Start", "Middle", "End", "Judgement"])
        dimension_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        dimension_table.verticalHeader().setVisible(False)
        dimension_table.setAlternatingRowColors(True)

        self.pellet_dimension_start = QLineEdit("2.5x3.5")
        dimension_table.setCellWidget(0, 0, self.pellet_dimension_start)
        self.pellet_dimension_middle = QLineEdit("2.6x3.5")
        dimension_table.setCellWidget(0, 1, self.pellet_dimension_middle)
        self.pellet_dimension_end = QLineEdit("2.5x3.5")
        dimension_table.setCellWidget(0, 2, self.pellet_dimension_end)
        self.pellet_dimension_judgement = QLineEdit("Passed")
        dimension_table.setCellWidget(0, 3, self.pellet_dimension_judgement)
        pellet_layout.addWidget(dimension_table)

        # Adjust table heights
        adjust_table_height_terumo(molded_table, appearance_table, dimension_table)

        main_v_layout.addWidget(pellet_group)

        # Remarks
        remarks_group = QGroupBox("Remarks")
        remarks_layout = QVBoxLayout()
        remarks_group.setLayout(remarks_layout)
        remarks_layout.setContentsMargins(10, 10, 10, 10)
        # Assuming self.terumo_remarks is a QTextEdit
        self.terumo_remarks.setPlaceholderText("Attached are the same sample chips for the following number: MB-24-5826AK")
        self.terumo_remarks.setText("Attached are the same sample chips for the following number:\nMB-24-5826AK")
        self.terumo_remarks.setMinimumHeight(60)
        remarks_layout.addWidget(self.terumo_remarks)
        main_v_layout.addWidget(remarks_group)

        # Approved By
        approved_group = QGroupBox("Approved By")
        approved_layout = QHBoxLayout()
        approved_group.setLayout(approved_layout)
        approved_layout.setContentsMargins(10, 10, 10, 10)
        # Assuming self.terumo_approved_by is a QLineEdit or QTextEdit
        self.terumo_approved_by.setText("Linzy Jam Bautista\nLaboratory Chemist")
        self.terumo_approved_by.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center align as in PDF
        self.terumo_approved_by.setMinimumHeight(50) # Give some height for two lines
        approved_layout.addWidget(self.terumo_approved_by)
        main_v_layout.addWidget(approved_group)

        # Submit Button
        submit_button_style = """
            QPushButton {
                background-color: #007bff;
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
                padding: 6px 16px;
                border: none;
                border-radius: 6px;
                min-width: 120px;
                min-height: 40px;
                transition: background-color 0.2s ease, box-shadow 0.2s ease;
            }
            QPushButton:hover {
                background-color: #0056b3;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:focus {
                outline: none;
                border: 2px solid #007bff;
            }
        """
        self.terumo_submit_btn.setStyleSheet(submit_button_style)

        submit_button_row = QHBoxLayout()
        submit_button_row.addStretch()
        submit_button_row.addWidget(self.terumo_submit_btn)
        submit_button_row.addStretch()
        main_v_layout.addLayout(submit_button_row)

        main_v_layout.addStretch(1)
        self.terumo_form_layout.addWidget(form_widget)
        clear_terumo_form(self)
    except Exception as e:
        print(f"Error loading Terumo form: {e}")

def adjust_table_height(self):
    self.summary_analysis_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    fixed_row_height = 48
    for i in range(self.summary_analysis_table.rowCount()):
        self.summary_analysis_table.setRowHeight(i, fixed_row_height)
    row_height_total = self.summary_analysis_table.rowCount() * fixed_row_height
    header_height = self.summary_analysis_table.horizontalHeader().height()
    table_border_thickness = 2
    self.summary_analysis_table.setFixedHeight(
        row_height_total + header_height + table_border_thickness + 4)

def adjust_table_height_terumo(*tables):
    fixed_row_height = 48
    table_border_thickness = 2
    for table in tables:
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        for i in range(table.rowCount()):
            table.setRowHeight(i, fixed_row_height)
        row_height_total = table.rowCount() * fixed_row_height
        header_height = table.horizontalHeader().height()
        table.setFixedHeight(row_height_total + header_height + table_border_thickness + 4)

def clear_coa_form(self):
    try:
        global current_coa_id
        current_coa_id = None
        self.color_code_input.blockSignals(True)
        self.delivery_receipt_input.blockSignals(True)
        self.coa_customer_input.clear()
        self.color_code_input.clear()
        self.lot_number_input.clear()
        self.po_number_input.clear()
        self.delivery_receipt_input.clear()
        self.quantity_delivered_input.clear()
        self.certified_by_input.clear()
        self.coa_storage_input.setText("Should be stored cool and dry in unbroken packaging.")
        self.coa_shelf_life_input.setText(
            "12 Months: Shelf life is stated as a maximum from the date of production when the product is stored in unbroken packaging.")
        self.suitability_input.setText("highly suitable for automotive oil container.")

        self.delivery_date_input.setDate(QDate.currentDate())
        self.production_date_input.setDate(QDate.currentDate())
        self.creation_date_input.setDate(QDate.currentDate())

        self.summary_analysis_table.clearContents()
        self.summary_analysis_table.setColumnCount(2)
        self.summary_analysis_table.setRowCount(3)
        self.summary_analysis_table.setHorizontalHeaderLabels(["Standard", "Delivery"])
        self.summary_analysis_table.setVerticalHeaderLabels([
            "Color", "Light Fastness (1-8)", "Heat Stability (1-5)"
        ])
        adjust_table_height(self)
        self.btn_coa_submit.setText("Submit")
        self.color_code_input.blockSignals(False)
        self.delivery_receipt_input.blockSignals(False)
    except Exception as e:
        print(str(e))

def clear_terumo_form(self):
    self.terumo_customer_input.clear()
    self.terumo_item_code.clear()
    self.terumo_item_desc.clear()
    self.terumo_lot_number.clear()
    self.terumo_quantity.clear()
    self.terumo_delivery_date.setDate(QDate.currentDate())
    self.terumo_remarks.clear()
    self.terumo_approved_by.clear()
    self.terumo_submit_btn.setText("Submit")

def populate_coa_fields(self, dr_no):
    try:
        fields = db_con.get_dr_details(dr_no)
        if not fields:
            self.coa_customer_input.clear()
            self.color_code_input.clear()
            self.po_number_input.clear()
            self.lot_number_input.clear()
            self.quantity_delivered_input.clear()
            self.delivery_date_input.setDate(QDate.currentDate())
            return

        lot_no = lot_format.normalize(fields[5])
        self.coa_customer_input.setText(str(fields[2]))
        self.color_code_input.setText(str(fields[1]))
        self.po_number_input.setText(str(fields[4]))
        self.lot_number_input.setText(lot_no)
        self.quantity_delivered_input.setText(str(fields[6]))

        if fields[3]:
            self.delivery_date_input.setDate(QDate(fields[3].year, fields[3].month, fields[3].day))
    except Exception as e:
        print(e)

def populate_coa_rrf_fields(self, rrf_no):
    self.delivery_receipt_input.blockSignals(True)
    try:
        fields = db_con.get_rrf_details(rrf_no)
        if not fields:
            self.coa_customer_input.clear()
            self.color_code_input.clear()
            self.po_number_input.clear()
            self.lot_number_input.clear()
            self.quantity_delivered_input.clear()
            self.delivery_date_input.setDate(QDate.currentDate())
            return
        self.coa_customer_input.setText(str(fields[2]))
        self.color_code_input.setText(str(fields[1]))
        self.quantity_delivered_input.setText(str(fields[5]))
        if fields[3]:
            self.delivery_date_input.setDate(QDate(fields[3].year, fields[3].month, fields[3].day))

        dr_pattern = r"DR\s*#\s*(\d+)"
        match = re.search(dr_pattern, str(fields[4]))
        global dr_num
        if match:
            dr_num = match.group(1)
        else:
            dr_num = ""

        add_lot_po = db_con.get_rrf_lot_po(dr_num)
        add_prod_date = db_con.get_rrf_prod_date(dr_num)

        if not add_lot_po:
            self.po_number_input.clear()
            self.lot_number_input.clear()
            self.production_date_input.setDate(QDate.currentDate())
            return

        lot_no = lot_format.normalize(add_lot_po[1])
        self.po_number_input.setText(str(add_lot_po[0]))
        self.lot_number_input.setText(lot_no)

        if add_prod_date[0]:
            self.production_date_input.setDate(
                QDate(add_prod_date[0].year, add_prod_date[0].month, add_prod_date[0].day))
    except Exception as e:
        print(e, "rrf fields")
    finally:
        self.delivery_receipt_input.blockSignals(False)

def populate_coa_summary(self):
    try:
        global dr_num
        color_code = self.color_code_input.text()
        if not self.is_rrf:
            dr_no = self.delivery_receipt_input.text()
        else:
            dr_no = dr_num
        result_color = db_con.get_summary_from_msds(color_code, dr_no)

        self.summary_analysis_table.clearContents()
        self.summary_analysis_table.setColumnCount(2)
        self.summary_analysis_table.setRowCount(3)

        self.summary_analysis_table.setHorizontalHeaderLabels(["Standard", "Delivery"])
        self.summary_analysis_table.setVerticalHeaderLabels([
            "Color", "Light Fastness (1-8)", "Heat Stability (1-5)"
        ])

        if not result_color:
            return

        color = str(result_color[1])
        self.summary_analysis_table.setItem(0, 0, QTableWidgetItem(str(color)))
        self.summary_analysis_table.setItem(0, 1, QTableWidgetItem(str(color)))

        table_details = db_con.get_coa_table_msds(result_color[0])
        self.summary_analysis_table.setItem(1, 0, QTableWidgetItem(str(table_details[0])))
        self.summary_analysis_table.setItem(1, 1, QTableWidgetItem(str(table_details[0])))
        self.summary_analysis_table.setItem(2, 0, QTableWidgetItem(str(table_details[1])))
        self.summary_analysis_table.setItem(2, 1, QTableWidgetItem(str(table_details[1])))

        adjust_table_height(self)
    except Exception as e:
        print(e)