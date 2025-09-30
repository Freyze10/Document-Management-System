import re

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QLabel, QHBoxLayout, QPushButton, QWidget, QVBoxLayout, QGroupBox, QGridLayout
)

from db import db_con
from utils import abs_path, lot_format

current_coa_id = None


def load_coa_details(self, coa_id):
    try:
        self.terumo_delivery_receipt.blockSignals(True)
        self.terumo_lot_number.blockSignals(True)
        self.terumo_item_description.blockSignals(True)

        field_result = db_con.get_single_coa_data(coa_id)
        terumo_res = db_con.get_single_terumo_data(coa_id)

        # === Populate inputs ===
        self.terumo_customer_input.setText(str(field_result[1]))
        self.terumo_lot_number.setText(str(field_result[3]))
        self.terumo_delivery_receipt.setText(str(field_result[5]))
        self.terumo_quantity.setText(str(field_result[6]))

        # Handle potential None for dates
        if field_result[7]:
            self.terumo_delivery_date.setDate(QDate(field_result[7].year, field_result[7].month, field_result[7].day))

        self.terumo_approved_by.setText(str(field_result[10]))
        self.terumo_approver_position.setText(str(terumo_res[22]))
        self.terumo_submit_btn.setText("Update")

        self.terumo_delivery_receipt.blockSignals(False)
        self.terumo_lot_number.blockSignals(False)

    #     for table
        diameter1, diameter2 = split_by_comma(str(terumo_res[7]))
        area1, area2 = split_by_comma(str(terumo_res[8]))
        count1, count2 = split_by_comma(str(terumo_res[9]))
        actual1, actual2 = split_by_comma(str(terumo_res[10]))

        self.terumo_item_code.setText(str(terumo_res[2]))
        self.terumo_item_description.setText(str(terumo_res[3]))
        self.terumo_color_std.setText(str(terumo_res[4]))
        self.terumo_color_actual.setText(str(terumo_res[5]))
        self.terumo_color_judgement.setText(str(terumo_res[6]))
        self.terumo_foreign_diameter1.setText(diameter1)
        self.terumo_foreign_diameter2.setText(diameter2)
        self.terumo_foreign_area1.setText(area1)
        self.terumo_foreign_area2.setText(area2)
        self.terumo_foreign_count1.setText(count1)
        self.terumo_foreign_count2.setText(count2)
        self.terumo_foreign_actual1.setText(actual1)
        self.terumo_foreign_actual2.setText(actual2)
        self.terumo_foreign_judgement.setText(str(terumo_res[11]))
        self.terumo_appearance_std.setText(str(terumo_res[12]))
        self.terumo_appearance_start.setText(str(terumo_res[13]))
        self.terumo_appearance_mid.setText(str(terumo_res[14]))
        self.terumo_appearance_end.setText(str(terumo_res[15]))
        self.terumo_appearance_judgement.setText(str(terumo_res[16]))
        self.terumo_dimension_std.setPlainText(str(terumo_res[17]))
        self.terumo_dimension_start.setText(str(terumo_res[18]))
        self.terumo_dimension_middle.setText(str(terumo_res[19]))
        self.terumo_dimension_end.setText(str(terumo_res[20]))
        self.terumo_dimension_judgement.setText(str(terumo_res[21]))
        self.terumo_lots.setPlainText(str(terumo_res[23]))
        self.terumo_item_description.blockSignals(False)
    except Exception as e:
        print(e)


def coa_entry_form(self):
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
            QLabel[class="subsection_title"] {{
                font-size: 16px;
                font-weight: 600;
                color: #212529;
                margin-top: 10px;
                margin-bottom: 8px;
            }}
            QLineEdit, QDateEdit, QTextEdit {{
                font-size: 12px;
                padding: 6px 8px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: #ffffff;
                min-height: 28px;
                selection-background-color: #aed6f1;
            }}
            QLineEdit:focus, QDateEdit:focus, QTextEdit:focus {{
                border: 1px solid #007bff;
                background-color: #e9f5ff;
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
            }}
            QTextEdit {{
                min-height: 100px;
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
        """)

        # === Header ===
        header = QLabel("Certificate of Analysis - Terumo")
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

        # === General Info ===
        general_info_group = QGroupBox()
        general_info_layout = QGridLayout()
        general_info_group.setLayout(general_info_layout)

        general_info_layout.setHorizontalSpacing(30)
        general_info_layout.setVerticalSpacing(15)
        general_info_layout.setContentsMargins(20, 25, 20, 20)

        # Rearranged to closer match PDF order
        general_info_layout.addWidget(QLabel("Delivery Receipt number:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.terumo_delivery_receipt, 0, 1)
        general_info_layout.addWidget(self.terumo_sync_button, 0, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        general_info_layout.addWidget(QLabel("Customer:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.terumo_customer_input, 1, 1)
        general_info_layout.addWidget(QLabel("Delivery Date:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.terumo_delivery_date, 1, 3)

        general_info_layout.addWidget(QLabel("Item Code:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.terumo_item_code, 2, 1)
        general_info_layout.addWidget(QLabel("Item Description:"), 2, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.terumo_item_description, 2, 3)

        general_info_layout.addWidget(QLabel("Lot No.:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.terumo_lot_number, 3, 1)
        general_info_layout.addWidget(QLabel("Quantity:"), 3, 2, Qt.AlignmentFlag.AlignRight)
        general_info_layout.addWidget(self.terumo_quantity, 3, 3)

        main_v_layout.addWidget(general_info_group)

        # === Molded Chip Inspection ===
        molded_group = QGroupBox("Molded Chip Inspection")
        molded_layout = QVBoxLayout()
        molded_group.setLayout(molded_layout)
        molded_layout.setContentsMargins(20, 25, 20, 20)
        molded_layout.setSpacing(15)

        # Color subsection
        color_title = QLabel("Color")
        color_title.setProperty("class", "subsection_title")
        molded_layout.addWidget(color_title)

        color_grid = QGridLayout()
        color_grid.setHorizontalSpacing(30)
        color_grid.setVerticalSpacing(10)
        color_grid.addWidget(QLabel("Standard:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.terumo_color_std, 0, 1)
        color_grid.addWidget(QLabel("Actual:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.terumo_color_actual, 0, 3)
        color_grid.addWidget(QLabel("Judgement:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        color_grid.addWidget(self.terumo_color_judgement, 1, 1)
        molded_layout.addLayout(color_grid)

        # Foreign Material Contamination subsection
        foreign_title = QLabel("Foreign Material Contamination")
        foreign_title.setProperty("class", "subsection_title")
        molded_layout.addWidget(foreign_title)

        foreign_grid = QGridLayout()
        foreign_grid.setHorizontalSpacing(30)
        foreign_grid.setVerticalSpacing(10)

        # Headers for columns
        foreign_grid.addWidget(QLabel(""), 0, 0, Qt.AlignmentFlag.AlignLeft)
        foreign_grid.addWidget(QLabel("Diameter (mm):"), 0, 1, Qt.AlignmentFlag.AlignLeft)
        foreign_grid.addWidget(QLabel("Area (mm²):"), 0, 2, Qt.AlignmentFlag.AlignLeft)
        foreign_grid.addWidget(QLabel("Count:"), 0, 3, Qt.AlignmentFlag.AlignLeft)
        foreign_grid.addWidget(QLabel("Actual:"), 0, 4, Qt.AlignmentFlag.AlignLeft)

        # Row 1
        foreign_grid.addWidget(QLabel(""), 1, 0)
        foreign_grid.addWidget(self.terumo_foreign_diameter1, 1, 1)
        foreign_grid.addWidget(self.terumo_foreign_area1, 1, 2)
        foreign_grid.addWidget(self.terumo_foreign_count1, 1, 3)
        foreign_grid.addWidget(self.terumo_foreign_actual1, 1, 4)

        # Row 2
        foreign_grid.addWidget(QLabel(""), 2, 0)
        foreign_grid.addWidget(self.terumo_foreign_diameter2, 2, 1)
        foreign_grid.addWidget(self.terumo_foreign_area2, 2, 2)
        foreign_grid.addWidget(self.terumo_foreign_count2, 2, 3)
        foreign_grid.addWidget(self.terumo_foreign_actual2, 2, 4)

        foreign_grid.addWidget(QLabel("Judgement:"), 3, 0, Qt.AlignmentFlag.AlignLeft)
        foreign_grid.addWidget(self.terumo_foreign_judgement, 3, 1, 1, 2)

        molded_layout.addLayout(foreign_grid)

        main_v_layout.addWidget(molded_group)

        # === Pellet Inspection ===
        pellet_group = QGroupBox("Pellet Inspection")
        pellet_layout = QVBoxLayout()
        pellet_group.setLayout(pellet_layout)
        pellet_layout.setContentsMargins(20, 25, 20, 20)
        pellet_layout.setSpacing(15)

        # Appearance subsection
        appearance_title = QLabel("Appearance")
        appearance_title.setProperty("class", "subsection_title")
        pellet_layout.addWidget(appearance_title)

        appearance_grid = QGridLayout()
        appearance_grid.setHorizontalSpacing(30)
        appearance_grid.setVerticalSpacing(10)
        appearance_grid.addWidget(QLabel("Standard:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        appearance_grid.addWidget(self.terumo_appearance_std, 0, 1, 1, 5)  # Span across
        appearance_grid.addWidget(QLabel("Start:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        appearance_grid.addWidget(self.terumo_appearance_start, 1, 1)
        appearance_grid.addWidget(QLabel("Middle:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        appearance_grid.addWidget(self.terumo_appearance_mid, 1, 3)
        appearance_grid.addWidget(QLabel("End:"), 1, 4, Qt.AlignmentFlag.AlignRight)
        appearance_grid.addWidget(self.terumo_appearance_end, 1, 5)
        appearance_grid.addWidget(QLabel("Judgement:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        appearance_grid.addWidget(self.terumo_appearance_judgement, 2, 1, 1, 2)
        pellet_layout.addLayout(appearance_grid)

        # Dimension subsection
        dimension_title = QLabel("Dimension")
        dimension_title.setProperty("class", "subsection_title")
        pellet_layout.addWidget(dimension_title)

        dimension_grid = QGridLayout()
        dimension_grid.setHorizontalSpacing(30)
        dimension_grid.setVerticalSpacing(10)
        dimension_grid.addWidget(QLabel("Standard:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        dimension_grid.addWidget(self.terumo_dimension_std, 0, 1, 1, 5)  # Span across
        dimension_grid.addWidget(QLabel("Start:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        dimension_grid.addWidget(self.terumo_dimension_start, 1, 1)
        dimension_grid.addWidget(QLabel("Middle:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        dimension_grid.addWidget(self.terumo_dimension_middle, 1, 3)
        dimension_grid.addWidget(QLabel("End:"), 1, 4, Qt.AlignmentFlag.AlignRight)
        dimension_grid.addWidget(self.terumo_dimension_end, 1, 5)
        dimension_grid.addWidget(QLabel("Judgement:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        dimension_grid.addWidget(self.terumo_dimension_judgement, 2, 1, 1, 2)
        pellet_layout.addLayout(dimension_grid)

        main_v_layout.addWidget(pellet_group)

        # === Remarks & Approved By ===
        remarks_group = QGroupBox("Remarks & Approval")
        remarks_layout = QGridLayout()
        remarks_group.setLayout(remarks_layout)
        remarks_layout.setHorizontalSpacing(30)
        remarks_layout.setVerticalSpacing(25)
        remarks_layout.setContentsMargins(20, 25, 20, 20)
        remarks_layout.addWidget(QLabel("Remarks: Attached are the same sample chips for the following number: "), 0, 0,
                                 1, 6, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        remarks_layout.addWidget(self.terumo_lots, 1, 0, 1, 6)
        self.terumo_lots.setStyleSheet("""
        min-height: 80px;
        """)
        label_approved = QLabel("Approved By: ")
        label_approved.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        label_position = QLabel("Position: ")
        label_position.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        remarks_layout.addWidget(label_approved, 2, 1)
        remarks_layout.addWidget(self.terumo_approved_by, 2, 2, 1, 2)

        remarks_layout.addWidget(label_position, 3, 1)
        remarks_layout.addWidget(self.terumo_approver_position, 3, 2, 1, 2)

        main_v_layout.addWidget(remarks_group)

        # === Submit Button ===
        submit_button_style = """
            QPushButton {
                background-color: #007bff;
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
                padding: 6px 12px;
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
        clear_coa_form(self)
        self.terumo_form_layout.addWidget(form_widget)
    except Exception as e:
        print(f"Error loading Terumo COA form: {e}")


def populate_terumo_coa_fields(self, dr_no):
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


def populate_item_code(self, item_desc):
    terumo_desc = item_desc.strip()
    mbpi_code = terumo_desc.split()[-1] if terumo_desc else ""

    terumo_item_code = db_con.get_terumo_item_code(mbpi_code)

    if terumo_item_code and len(terumo_item_code) > 0:
        self.terumo_item_code.setText(str(terumo_item_code[0]))
    else:
        self.terumo_item_code.setText("")


def clear_coa_form(self):
    try:
        """Clear all input fields and the summary table."""
        global current_coa_id
        current_coa_id = None
        self.terumo_delivery_receipt.blockSignals(True)
        self.terumo_lot_number.blockSignals(True)

        self.terumo_customer_input.clear()
        self.terumo_lot_number.clear()
        self.terumo_quantity.clear()
        self.terumo_delivery_date.setDate(QDate.currentDate())
        self.terumo_item_code.clear()
        self.terumo_item_description.clear()
        self.terumo_delivery_receipt.clear()
        self.terumo_approved_by.clear()
        self.terumo_approver_position.clear()
        self.terumo_lots.clear()

        self.terumo_submit_btn.setText("Submit")
        self.terumo_delivery_receipt.blockSignals(False)
        self.terumo_lot_number.blockSignals(False)
    except Exception as e:
        print(str(e))


def seperate_lots(self, lot):
    inner_text = lot
    match = re.search(r"\((.*?)\)", lot)
    if match:
        inner_text = match.group(1)
    if re.search(r"\d+[A-Z]*-\d+[A-Z]*", inner_text):
        inner_text = lot_format.normalize(inner_text)
    expanded_lot = lot_format.expand_lots(inner_text)
    self.terumo_lots.setPlainText(expanded_lot)


def split_by_comma(text: str):
    # Split by comma and strip spaces
    return [part.strip() for part in text.split(",") if part.strip()]