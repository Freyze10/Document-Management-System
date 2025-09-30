from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QGroupBox, QGridLayout, QPushButton, QTextEdit, \
    QLineEdit
from PyQt6.QtCore import Qt, QDate

from alert import window_alert
from db import db_con


def populate_korpack_coa_fields(self, dr_no):
    try:
        fields = db_con.get_dr_details(dr_no)

        if not fields:  # None or empty tuple
            # Clear fields or just exit
            self.terumo_customer_input.clear()

            self.terumo_lot_number.clear()
            self.terumo_quantity.clear()
            self.terumo_delivery_date.setDate(QDate.currentDate())

            self.terumo_item_code.clear()
            self.terumo_item_description.clear()
            return

        # === Populate inputs ===
        lot_no = lot_format.normalize(fields[5])
        item_desc = db_con.get_trade_name_msds(fields[1])
        if item_desc:
            desc = item_desc[0]
        else:
            desc = ""
        self.terumo_item_description.setText(str(desc))

        self.terumo_customer_input.setText(str(fields[2]))
        self.terumo_quantity.setText(str(fields[6]))
        self.terumo_lot_number.setText(lot_no)

        if fields[3]:
            self.terumo_delivery_date.setDate(QDate(fields[3].year, fields[3].month, fields[3].day))

    except Exception as e:
        print("terumo", e)

def create_korpack_form(self):
    """Create the Korpack Certificate of Analysis (COA) form."""
    form_widget = QWidget()
    main_v_layout = QVBoxLayout(form_widget)
    main_v_layout.setContentsMargins(30, 20, 30, 30)  # Consistent padding

    # Apply stylesheet similar to MSDS form
    form_widget.setStyleSheet("""
        QWidget {
            background-color: #f8f9fa;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            color: #343a40;
        }
        QLabel {
            font-size: 12px;
            font-weight: 600;
            color: #495057;
            padding-bottom: 2px;
            background-color: transparent;
        }
        QLabel#mainHeader {
            font-size: 32px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 30px;
            padding-bottom: 10px;
            border-bottom: 3px solid #007bff;
            text-align: center;
        }
        QLineEdit, QTextEdit, QDateEdit {
            font-size: 12px;
            padding: 4px 8px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            background-color: #ffffff;
            min-height: 26px;
            selection-background-color: #aed6f1;
            color: #343a40;
        }
        QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {
            border: 1px solid #007bff;
            background-color: #e9f5ff;
            box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
        }
        QLineEdit.empty_field, QTextEdit.empty_field {
            border: 1px solid #dc3545;
            background-color: #ffebeb;
        }
        QLineEdit.empty_field:focus, QTextEdit.empty_field:focus {
            border: 1px solid #dc3545;
            box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.25);
        }
        QLineEdit#drNoField {
            max-width: 150px; /* Shortened width for korpack_dr_no */
        }
        QTextEdit {
            min-height: 80px;
            max-height: 120px;
            vertical-align: top;
        }
        QGroupBox {
            font-size: 14px;
            font-weight: 600;
            color: #212529;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-top: 2.0ex;
            background-color: #ffffff;
            padding: 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 10px;
            left: 15px;
            margin-left: 0px;
            color: #34495e;
        }
        QPushButton {
            background-color: #007bff;
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            min-width: 80px;
            min-height: 30px;
            margin-top: 20px;
            letter-spacing: 0.5px;
        }
        QPushButton:hover {
            background-color: #0056b3;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        QPushButton:pressed {
            background-color: #004085;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        QPushButton:focus {
            outline: none;
            border: 2px solid #5dade2;
        }
    """)
    sync_style = """
                QPushButton {
                    background-color: #28a745; /* Green sync button */
                    color: white;
                    font-size: 12px; /* Slightly smaller font */
                    font-weight: 500;
                    padding: 6px 8px; /* Adjusted padding */
                    border: none;
                    border-radius: 6px;
                    min-width: 50px; /* Adjusted min-width */
                    max-width: 65px; /* Adjusted max-width */
                    min-height: 24px; /* Slightly smaller height */
                }
                QPushButton:hover { background-color: #218838; }
                QPushButton:pressed { background-color: #1e7e34; }
            """
    # Header
    header = QLabel("Certificate of Analysis - Korpack")
    header.setObjectName("mainHeader")
    header_layout = QHBoxLayout()
    header_layout.addStretch()
    header_layout.addWidget(header)
    header_layout.addStretch()
    main_v_layout.addLayout(header_layout)

    # Helper function to create form groups
    def create_form_group(title, fields):
        group = QGroupBox(title)
        layout = QGridLayout()
        layout.setHorizontalSpacing(30)
        layout.setVerticalSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)
        row_idx = 0
        for label_text, input_widget in fields:
            if label_text == "Delivery Receipt:":  # Special handling for korpack_dr_no
                # Create a horizontal layout for the field and sync button
                dr_layout = QHBoxLayout()
                label = QLabel(label_text)
                self.korpack_dr_no.setObjectName("drNoField")  # Apply shortened width
                dr_layout.addWidget(self.korpack_dr_no, alignment=Qt.AlignmentFlag.AlignBottom)
                sync_button = QPushButton("Sync")
                sync_button.setStyleSheet(sync_style)
                sync_button.clicked.connect(lambda: self.run_sync_script())
                dr_layout.addWidget(sync_button)
                dr_layout.addStretch()  # Push button to the right
                layout.addWidget(label, row_idx, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                layout.addLayout(dr_layout, row_idx, 1)
            else:
                if label_text:
                    label = QLabel(label_text)
                    layout.addWidget(label, row_idx, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    layout.addWidget(input_widget, row_idx, 1)
                else:
                    layout.addWidget(input_widget, row_idx, 0, 1, 2)
            # Connect validation signals
            if isinstance(input_widget, QLineEdit):
                input_widget.textChanged.connect(lambda text, widget=input_widget: validate_field(widget))
            elif isinstance(input_widget, QTextEdit):
                input_widget.textChanged.connect(lambda: validate_field(input_widget))
            row_idx += 1
        group.setLayout(layout)
        return group

    # Section 1: Product Information
    product_info_fields = [
        ("Delivery Receipt:", self.korpack_dr_no),
        ("Customer Name:", self.korpack_customer),
        ("Product Name:", self.korpack_product_name),
        ("Lot Number:", self.korpack_lot_number),
        ("Quantity Delivered:", self.korpack_quantity_delivered),
        ("Manufacturing Date:", self.korpack_manufacturing_date),
        ("Delivery Date:", self.korpack_delivery_date),
    ]
    main_v_layout.addWidget(create_form_group("1) Product Information", product_info_fields))

    # Section 2: Physical Properties
    physical_properties_fields = [
        ("Physical Form:", self.korpack_physical_form),
        ("Heat Suitability:", self.korpack_heat_suitability),
        ("Light Fastness:", self.korpack_light_fastness),
        ("Migration:", self.korpack_migration),
        ("Swatch Dosage:", self.korpack_swatch_dosage),
        ("Product Application:", self.korpack_product_application),
        ("Packaging Form:", self.korpack_packaging_form),
    ]
    main_v_layout.addWidget(create_form_group("2) Physical Properties", physical_properties_fields))

    # Section 3: Regulatory and Approval Information
    regulatory_approval_fields = [
        ("Regulatory Information:", self.korpack_regulatory_info),
        ("Approved By:", self.korpack_approved_by),
        ("Approver Position:", self.korpack_approver_position),
    ]
    main_v_layout.addWidget(create_form_group("3) Regulatory and Approval Information", regulatory_approval_fields))

    # Submit Button
    submit_button_row = QHBoxLayout()
    submit_button_row.addStretch()
    submit_button_row.addWidget(self.korpack_btn_submit)
    submit_button_row.addStretch()
    main_v_layout.addLayout(submit_button_row)
    main_v_layout.addStretch(1)

    # Add form widget to the main layout (assuming self.korpack_form_layout exists)
    self.korpack_form_layout.addWidget(form_widget)

    # Perform initial validation
    check_empty_fields(self)

def validate_field(widget):
    """Validate if a QLineEdit or QTextEdit is empty and apply/remove red border."""
    is_empty = False
    if isinstance(widget, QLineEdit):
        is_empty = not widget.text().strip()
    elif isinstance(widget, QTextEdit):
        is_empty = not widget.toPlainText().strip()

    if is_empty:
        if widget.property("class") != "empty_field":
            widget.setProperty("class", "empty_field")
            widget.style().polish(widget)
    else:
        if widget.property("class") == "empty_field":
            widget.setProperty("class", "")
            widget.style().polish(widget)

def check_empty_fields(self):
    """Apply validation to all relevant input fields in the form."""
    input_fields = [
        self.korpack_customer,
        self.korpack_product_name,
        self.korpack_lot_number,
        self.korpack_quantity_delivered,
        self.korpack_physical_form,
        self.korpack_heat_suitability,
        self.korpack_light_fastness,
        self.korpack_migration,
        self.korpack_swatch_dosage,
        self.korpack_product_application,
        self.korpack_packaging_form,
        self.korpack_regulatory_info,
        self.korpack_approved_by,
        self.korpack_approver_position,
    ]
    for field in input_fields:
        validate_field(field)

def clear_korpack_form(self):
    """Clear all input fields in the Korpack COA form."""
    try:
        # Clear QLineEdit and QTextEdit fields
        for widget in [
            self.korpack_customer,
            self.korpack_product_name,
            self.korpack_lot_number,
            self.korpack_quantity_delivered,
            self.korpack_physical_form,
            self.korpack_heat_suitability,
            self.korpack_light_fastness,
            self.korpack_migration,
            self.korpack_swatch_dosage,
            self.korpack_product_application,
            self.korpack_packaging_form,
            self.korpack_approved_by,
            self.korpack_approver_position,
            self.korpack_regulatory_info,
        ]:
            widget.blockSignals(True)
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QTextEdit):
                widget.setPlainText("")
            widget.blockSignals(False)
            if widget.property("class") == "empty_field":
                widget.setProperty("class", "")
                widget.style().polish(widget)

        # Reset QDateEdit fields to current date
        self.korpack_regulatory_info.setPlainText(
            "• Chemically stable & non reactive. \n"
            "• Non-toxic & physiologically harmless. \n"
            "• Conform to product waste disposal under local regulation."
        )
        self.korpack_manufacturing_date.setDate(QDate.currentDate())
        self.korpack_delivery_date.setDate(QDate.currentDate())

        self.korpack_btn_submit.setText("Submit")
        check_empty_fields(self)
    except Exception as e:
        # Assuming window_alert is available as in MSDS
        window_alert.show_message(self, "Unexpected Error", f"An error occurred: {str(e)}", icon_type="critical")