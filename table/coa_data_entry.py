import re

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QLabel, QHBoxLayout, QHeaderView, QPushButton, QTableWidgetItem,
    QAbstractItemView, QWidget, QVBoxLayout, QGroupBox, QGridLayout  # Import QGridLayout
)
from db import db_con
from utils import abs_path, lot_format
from utils.check_cx import match_customer, note_summary_table

current_coa_id = None


def load_coa_details(self, coa_id, is_rrf):
    self.coa_customer_input.blockSignals(True)
    self.color_code_input.blockSignals(True)
    self.delivery_receipt_input.blockSignals(True)
    if is_rrf:
        field_result = db_con.get_single_coa_data_rrf(coa_id)
        analysis_table_result = db_con.get_coa_analysis_results_rrf(coa_id)
    else:
        field_result = db_con.get_single_coa_data(coa_id)
        analysis_table_result = db_con.get_coa_analysis_results(coa_id)

    # === Populate inputs ===
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
        self.production_date_input.display_value(str(field_result[8]))
    if field_result[9]:
        self.creation_date_input.setDate(QDate(field_result[9].year, field_result[9].month, field_result[9].day))

    self.certified_by_input.setText(str(field_result[10]))
    self.coa_storage_input.setText(str(field_result[11]))
    self.coa_shelf_life_input.setText(str(field_result[12]))
    self.suitability_input.setText(str(field_result[13]))
    if field_result[15]:
        self.coa_others_input.setText(str(field_result[15]))
    if field_result[16]:
        match_customer(self, self.coa_customer_input.text())
        self.zp_code_input.setText(str(field_result[16]))
    if field_result[17]:
        self.date_evaluated_input.setDate(QDate(field_result[17].year, field_result[17].month, field_result[17].day))
    self.btn_coa_submit.setText("Update")
    self.btn_save_as_new.setVisible(True)

    # === Populate table ===
    self.summary_analysis_table.clearContents()
    self.summary_analysis_table.setRowCount(len(analysis_table_result))
    self.summary_analysis_table.setColumnCount(2)
    self.summary_analysis_table.setHorizontalHeaderLabels(["Standard Value", "Delivery Value"])

    for row_idx, (parameter_name, standard_value, delivery_value) in enumerate(analysis_table_result):
        self.summary_analysis_table.setVerticalHeaderItem(row_idx, QTableWidgetItem(parameter_name))
        self.summary_analysis_table.setItem(row_idx, 0, QTableWidgetItem(str(standard_value) if standard_value else ""))
        self.summary_analysis_table.setItem(row_idx, 1, QTableWidgetItem(str(delivery_value) if delivery_value else ""))

    adjust_table_height(self)
    self.delivery_receipt_input.blockSignals(False)


def enable_auto_fill(self):
    self.coa_customer_input.blockSignals(False)
    self.color_code_input.blockSignals(False)


def coa_data_entry_form(self, is_rrf=False):
    try:
        form_widget = QWidget()
        main_v_layout = QVBoxLayout(form_widget)  # Use QVBoxLayout for overall structure
        main_v_layout.setContentsMargins(30, 20, 30, 30)
        calendar_icon_path = abs_path.resource("img/calendar_icon.png").replace("\\", "/")

        form_widget.setStyleSheet(f"""
            QWidget {{
                background-color: #f8f9fa; /* Very light background for the whole form */
                font-family: 'Inter', 'Segoe UI', sans-serif; /* Modern font */
                color: #343a40; /* Dark gray for general text */
            }}
            QLabel {{
                font-size: 14px;
                font-weight: 500;
                color: #495057; /* Slightly darker gray for labels */
                padding-bottom: 2px; /* Small padding below labels */
                background-color: transparent;
            }}
            QLabel[class="section_title"] {{ /* New class for section titles - now handled by QGroupBox */
                font-size: 18px;
                font-weight: 600;
                color: #212529; /* Very dark for section titles */
                margin-top: 10px;
                margin-bottom: 16px;
                padding-bottom: 5px;
                text-align: center; 
            }}
            QLineEdit, QDateEdit, QTextEdit {{
                font-size: 12px;
                padding: 6px 8px;
                border: 1px solid #ced4da; /* Lighter, more neutral border */
                border-radius: 6px; /* Slightly less rounded for a crisp look */
                background-color: #ffffff;
                min-height: 28px; /* Consistent height */
                selection-background-color: #aed6f1;
            }}
            QLineEdit:focus, QDateEdit:focus, QTextEdit:focus {{
                border: 1px solid #007bff; /* Primary blue on focus */
                background-color: #e9f5ff; /* Very light blue background on focus */
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25); /* Subtle focus ring */
            }}
            QDateEdit::drop-down {{
                border: 0px;
                width: 40px; /* Slightly wider dropdown button */
                background-color: #e9ecef; /* Light gray background for dropdown */
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QDateEdit::down-arrow {{
                background-image: url("{calendar_icon_path}"); /* Ensure this path is correct */
                width: 26px;
                height: 26px;
            }}
            QDateEdit::drop-down:hover {{
                background-color: #dee2e6; /* Slightly darker on hover */
            }}

            QDateEdit::down-arrow:on {{
                top: 1px;
                left: 1px;
            }}
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: #212529;
                border: 1px solid #e0e0e0; /* Lighter border for group box */
                border-radius: 8px;
                margin-top: 2.0ex; /* Space for title */
                background-color: #ffffff;
                padding: 10px; /* Inner padding for group box content */
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px; /* Wider padding for title text */
                left: 15px; /* Adjust title position */
                margin-left: 0px; /* No margin here, padding takes over */
                color: #34495e;
                background-color: #f8f9fa; /* Match widget background for cutout effect */
            }}
        """)

        # === Header ===
        header = self.coa_header_label
        header.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 30px;
            padding-bottom: 10px;
            border-bottom: 3px solid #007bff; /* Primary blue underline */
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

        # Row 0
        general_info_layout.addWidget(QLabel("Customer:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.coa_customer_input, 0, 1)
        general_info_layout.addWidget(QLabel("Color Code:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.color_code_input, 0, 3)

        # Row 0, cols 4 & 5 (after Color Code)
        general_info_layout.addWidget(self.zp_code_label, 0, 4, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.zp_code_input, 0, 5)

        # Row 1
        general_info_layout.addWidget(QLabel("Lot Number:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.lot_number_input, 1, 1)
        general_info_layout.addWidget(QLabel("Quantity Delivered:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.quantity_delivered_input, 1, 3)

        # Row 2: Delivery Receipt & PO Number
        general_info_layout.addWidget(self.delivery_receipt_label, 2, 0, Qt.AlignmentFlag.AlignRight)
        receipt_input_layout = QHBoxLayout()
        receipt_input_layout.addWidget(self.delivery_receipt_input, alignment=Qt.AlignmentFlag.AlignVCenter)
        sync_style = """
            QPushButton {
                background-color: #28a745; /* Green sync button */
                color: white;
                font-size: 13px; /* Slightly smaller font */
                font-weight: 500;
                padding: 6px 8px; /* Adjusted padding */
                border: none;
                border-radius: 6px;
                min-width: 50px; /* Adjusted min-width */
                max-width: 65px; /* Adjusted max-width */
                min-height: 28px; /* Slightly smaller height */
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:pressed { background-color: #1e7e34; }
        """
        sync_update_style = """
            QPushButton {
                background-color: #1976D2; /* same as rrf button */
                color: white;
                font-size: 13px; /* Slightly smaller font */
                font-weight: 500;
                padding: 6px 8px; /* Adjusted padding */
                border: none;
                border-radius: 6px;
                min-width: 50px; /* Adjusted min-width */
                max-width: 65px; /* Adjusted max-width */
                min-height: 28px; /* Slightly smaller height */
            }
            QPushButton:hover { background-color: #1565C0; }
            QPushButton:pressed { background-color: #0D47A1; }
        """

        self.sync_button.setStyleSheet(sync_style)
        self.terumo_sync_button.setStyleSheet(sync_style)
        self.sync_update_button.setStyleSheet(sync_update_style)
        receipt_input_layout.addWidget(self.sync_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        receipt_input_layout.addWidget(self.sync_update_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        general_info_layout.addLayout(receipt_input_layout, 2, 1)

        general_info_layout.addWidget(QLabel("P.O Number:"), 2, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.po_number_input, 2, 3)

        # Row 3: Dates
        general_info_layout.addWidget(QLabel("Delivery Date:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.delivery_date_input, 3, 1)
        general_info_layout.addWidget(QLabel("Production Date:"), 3, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.production_date_input, 3, 3)
        general_info_layout.addWidget(self.date_evaluated_label, 3, 4, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.date_evaluated_input, 3, 5)
        general_info_layout.addWidget(self.plastimer_expiry_label, 3, 4, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.plastimer_expiry_input, 3, 5)

        main_v_layout.addWidget(general_info_group)

        # === Section 2: Summary of Analysis ===
        summary_analysis_group = QGroupBox()
        summary_analysis_layout = QVBoxLayout()
        summary_analysis_group.setLayout(summary_analysis_layout)
        summary_analysis_layout.setContentsMargins(20, 25, 20, 20)

        section2_header = QLabel("Summary of Analysis")
        section2_header.setProperty("class", "section_title")

        self.summary_analysis_table.setColumnCount(2)
        self.summary_analysis_table.setRowCount(3)
        self.summary_analysis_table.setHorizontalHeaderLabels(["Standard", "Delivery"])
        self.summary_analysis_table.setVerticalHeaderLabels(self.summary_initial_v_header)
        self.summary_analysis_table.setMinimumWidth(650)
        self.summary_analysis_table.setMaximumWidth(850)
        self.summary_analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.summary_analysis_table.resizeRowsToContents()
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

        # === Buttons for table ===
        btn_add_row = QPushButton("Add Row")
        btn_add_row.clicked.connect(self.add_row_to_coa_summary_table)
        btn_delete_row = QPushButton("Delete Row")
        btn_delete_row.clicked.connect(self.delete_row_from_coa_summary_table)
        btn_delete_row.setProperty("class", "delete")

        button_style = """
            QPushButton {
                background-color: #28a745; /* Green for add */
                color: #ffffff;
                font-size: 14px; /* Slightly smaller font */
                font-weight: 600;
                padding: 6px 12px; /* Adjusted padding */
                border: none;
                border-radius: 6px;
                min-width: 80px; /* Adjusted min-width */
                min-height: 30px; /* Adjusted min-height */
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
                background-color: #dc3545; /* Red for delete */
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
        submit_button_style = button_style.replace("#28a745", "#007bff")  # Blue for submit
        submit_button_style = submit_button_style.replace("#218838", "#0056b3")  # Darker blue hover
        submit_button_style = submit_button_style.replace("#1e7e34", "#004085")  # Even darker blue pressed
        submit_button_style = submit_button_style.replace("min-width: 80px;",
                                                          "min-width: 90px;")
        self.btn_coa_submit.setStyleSheet(submit_button_style)

        btn_add_table_row = QHBoxLayout()
        btn_add_table_row.addStretch()
        btn_add_table_row.addWidget(btn_add_row)
        btn_add_table_row.addSpacing(10)
        btn_add_table_row.addWidget(btn_delete_row)
        btn_add_table_row.addStretch()
        summary_analysis_layout.addLayout(btn_add_table_row)

        main_v_layout.addWidget(summary_analysis_group)

        # === Section 3: Certification & Other Info ===
        certification_group = QGroupBox()
        certification_layout = QGridLayout()  # Using QGridLayout here too
        certification_group.setLayout(certification_layout)
        certification_layout.setHorizontalSpacing(30)
        certification_layout.setVerticalSpacing(15)
        certification_layout.setContentsMargins(20, 25, 20, 20)
        self.coa_others_input.setStyleSheet("""
                min-height: 72px;
            """)

        # Certified by and Creation Date
        certification_layout.addWidget(QLabel("Certified by:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.certified_by_input, 0, 1)
        certification_layout.addWidget(QLabel("Date:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.creation_date_input, 0, 3)

        # Storage and Shelf Life
        certification_layout.addWidget(QLabel("Storage:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.coa_storage_input, 1, 1)
        certification_layout.addWidget(QLabel("Suitability:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.suitability_input, 1, 3)

        # Suitability
        certification_layout.addWidget(QLabel("Shelf Life:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.coa_shelf_life_input, 2, 1, 1, 3)  # Span across remaining columns
        certification_layout.addWidget(QLabel(""), 3, 0, Qt.AlignmentFlag.AlignRight)
        certification_layout.addWidget(self.coa_others_input, 3, 1, 1, 3)  # Span across remaining columns

        main_v_layout.addWidget(certification_group)

        # === Submit Button ===
        submit_button_row = QHBoxLayout()
        submit_button_row.addStretch()

        self.btn_save_as_new = QPushButton("Save as New")
        save_as_new_style = button_style.replace("#28a745", "#17a2b8")  # Info blue for save as new
        save_as_new_style = save_as_new_style.replace("#218838", "#138496")  # Darker info blue hover
        save_as_new_style = save_as_new_style.replace("#1e7e34", "#117a8b")  # Even darker info blue pressed
        save_as_new_style = save_as_new_style.replace("min-width: 80px;", "min-width: 90px;")
        self.btn_save_as_new.setStyleSheet(save_as_new_style)
        self.btn_save_as_new.setVisible(False)
        self.btn_save_as_new.clicked.connect(self.save_as_new_clicked)

        submit_button_row.addWidget(self.btn_save_as_new)
        submit_button_row.addSpacing(10)

        submit_button_row.addWidget(self.btn_coa_submit)
        submit_button_row.addSpacing(10)

        self.btn_print = QPushButton("Print")
        print_style = button_style.replace("#28a745", "#6c757d")  # Gray for print
        print_style = print_style.replace("#218838", "#5a6268")  # Darker gray hover
        print_style = print_style.replace("#1e7e34", "#545b62")  # Even darker gray pressed
        print_style = print_style.replace("min-width: 80px;", "min-width: 90px;")
        self.btn_print.setStyleSheet(print_style)
        self.btn_print.clicked.connect(lambda: self.coa_btn_submit_clicked(print_after=True))
        submit_button_row.addWidget(self.btn_print)

        submit_button_row.addStretch()
        main_v_layout.addLayout(submit_button_row)

        main_v_layout.addStretch(1)

        self.coa_form_layout.addWidget(form_widget)
        clear_coa_form(self)
    except Exception as e:
        print(f"Error loading COA form: {e}")


def adjust_table_height(self):
    self.summary_analysis_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

    # Calculate actual row height considering padding and borders from stylesheet
    fixed_row_height = 48
    vertical_headers = []
    for i in range(self.summary_analysis_table.rowCount()):
        self.summary_analysis_table.setRowHeight(i, fixed_row_height)
        header_text = self.summary_analysis_table.verticalHeaderItem(i)
        if header_text:
            vertical_headers.append(header_text.text())
        else:
            vertical_headers.append("")  # in case the header is missing
    row_height_total = self.summary_analysis_table.rowCount() * fixed_row_height
    header_height = self.summary_analysis_table.horizontalHeader().height()

    note_summary_table(self, vertical_headers, self.coa_customer_input.text())
    table_border_thickness = 2
    self.summary_analysis_table.setFixedHeight(
        row_height_total + header_height + table_border_thickness + 4)


def clear_coa_form(self):
    try:
        """Clear all input fields and the summary table."""
        global current_coa_id
        current_coa_id = None
        self.coa_customer_input.blockSignals(True)
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
            "12 months: Shelf life is stated as a maximum from the date of production when the product is stored in unbroken packaging.")
        self.suitability_input.setText("")
        self.coa_others_input.clear()
        self.zp_code_input.clear()
        self.date_evaluated_input.clear()

        self.delivery_date_input.setDate(QDate.currentDate())
        self.production_date_input.clear_value()
        self.creation_date_input.setDate(QDate.currentDate())

        self.summary_analysis_table.clearContents()
        self.summary_analysis_table.setColumnCount(2)
        self.summary_analysis_table.setRowCount(3)
        self.summary_analysis_table.setHorizontalHeaderLabels(["Standard", "Delivery"])
        self.summary_initial_v_header = ["Color", "Light Fastness (1-8)", "Heat Stability (1-5)"]
        self.summary_analysis_table.setVerticalHeaderLabels(self.summary_initial_v_header)
        adjust_table_height(self)
        self.btn_coa_submit.setText("Submit")
        self.btn_save_as_new.setVisible(False)
        self.coa_customer_input.blockSignals(False)
        self.color_code_input.blockSignals(False)
        self.delivery_receipt_input.blockSignals(False)
    except Exception as e:
        print(str(e))


def populate_coa_fields(self, dr_no):
    try:
        records = db_con.get_dr_details(dr_no)
        if not records:
            # No data, clear fields
            self.coa_customer_input.clear()
            self.color_code_input.clear()
            self.po_number_input.clear()
            self.lot_number_input.clear()
            self.quantity_delivered_input.clear()
            self.zp_code_input.clear()
            self.date_evaluated_input.clear()
            self.delivery_date_input.setDate(QDate.currentDate())
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

        # === Populate inputs ===
        lot_no = lot_format.normalize(selected_record[5])

        self.coa_customer_input.setText(str(selected_record[2]))
        self.color_code_input.setText(str(selected_record[1]))
        self.po_number_input.setText(str(selected_record[4]))
        self.lot_number_input.setText(lot_no)
        self.quantity_delivered_input.setText(str(selected_record[6]))

        if selected_record[3]:
            self.delivery_date_input.setDate(
                QDate(selected_record[3].year, selected_record[3].month, selected_record[3].day)
            )

        # for bottom note
        match_customer(self, selected_record[2])
        adjust_table_height(self)

    except Exception as e:
        print("Error in populate_coa_fields:", e)


global dr_num


def populate_coa_rrf_fields(self, rrf_no):
    self.delivery_receipt_input.blockSignals(True)
    try:
        fields = db_con.get_rrf_details(rrf_no)

        if not fields:  # if None or empty
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

        if not add_lot_po:  # None or empty
            self.po_number_input.clear()
            self.lot_number_input.clear()
            self.production_date_input.clear_value()
            return

        # === Populate inputs ===

        lot_no = lot_format.normalize(add_lot_po[1])

        self.po_number_input.setText(str(add_lot_po[0]))
        self.lot_number_input.setText(lot_no)

        if add_prod_date[0]:
            self.production_date_input.display_value(str(add_prod_date[0]))
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

        # Clear and reset table
        self.summary_analysis_table.clearContents()
        self.summary_analysis_table.setColumnCount(2)
        self.summary_analysis_table.setRowCount(3)

        # Always keep the same headers
        self.summary_analysis_table.setHorizontalHeaderLabels(["Standard", "Delivery"])
        self.summary_analysis_table.setVerticalHeaderLabels(self.summary_initial_v_header)

        # # If nothing found → just return (empty table with headers)
        # if self.is_zeller:
        #     zeller_item_code = db_con.get_zeller_item_code(self.color_code_input.text())
        #     if zeller_item_code:
        #         # Extract the string from the tuple
        #         zeller_text = zeller_item_code[0]
        #         zeller_code = zeller_text.split()[-1]  # Get the last part (e.g., ZP4087)
        #
        #         self.zp_code_input.setText(zeller_code)
        #     else:
        #         self.zp_code_input.clear()
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