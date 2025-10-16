import re

from PyQt6.QtCore import QDate, Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QLabel, QHBoxLayout, QHeaderView, QTableWidgetItem, QLineEdit,
    QAbstractItemView, QWidget, QVBoxLayout, QGroupBox, QGridLayout,
    QTableWidget, QScrollArea, QDateEdit, QPushButton, QCompleter
)
from alert import window_alert
from db import db_dr, db_con
from table import table
from utils import abs_path, lot_format, multiple_dates, prod_date_format  # Assuming utils is available with abs_path
from utils.loading import LoadingDialog
from utils.debounce import setup_finished_typing
from print.print_packageworld_rowell import FileRowell

current_coa_id = None


class RowellWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.default_values()
        self.rowell_widget = None

    def setup_ui(self):
        # Main container with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

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
        header = QLabel("""Certificate of Inspection\nPVC-FREE COMPOUND FOOD APPROVED""")
        header.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 30px;
            padding-bottom: 10px;
            border-bottom: 3px solid #007bff;
            text-align: center;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.delivery_date = QDateEdit()
        self.delivery_date.setDate(QDate.currentDate())
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
        self.certified_by_lists = db_con.get_all_certified_by()
        # Create QCompleter with the list
        style_completer = """
                    QListView {
                        background-color: white;
                        border: 1px solid gray;
                        font-size: 12px;
                        padding: 4px;
                    }
                    QListView::item {
                        padding: 6px;
                    }
                    QListView::item:hover{
                        background-color: lightgrey;
                    }
                    QListView::item:selected {
                        background-color: #0078d7;  /* Windows blue */
                        color: white;
                    }
                """
        self.certified_completer = QCompleter(self.certified_by_lists)
        self.certified_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.certified_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.certified_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.certified_completer.setCurrentRow(0)
        self.certified_completer.popup().setStyleSheet(style_completer)
        self.certified_by_name_input.setCompleter(self.certified_completer)


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

        self.btn_save_as_new = QPushButton("Save as New")
        self.btn_save_as_new.setStyleSheet("""
                    QPushButton {
                        background-color: #17a2b8;
                    }
                    QPushButton:hover {
                        background-color: #138496;
                    }
                    QPushButton:pressed {
                        background-color: #117a8b;
                    }
                """)
        self.btn_save_as_new.clicked.connect(self.rowell_save_as_new_clicked)
        self.btn_save_as_new.setVisible(False)
        submit_button_row.addWidget(self.btn_save_as_new)

        self.btn_submit = QPushButton("Submit")
        self.btn_submit.clicked.connect(self.on_submit_clicked)
        submit_button_row.addWidget(self.btn_submit)

        self.btn_print = QPushButton("Print")
        self.btn_print.setStyleSheet("""
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
        self.btn_print.clicked.connect(lambda: self.on_submit_clicked(print_after=True))
        submit_button_row.addWidget(self.btn_print)

        submit_button_row.addStretch()
        main_v_layout.addLayout(submit_button_row)

        main_v_layout.addStretch(1)

        # Set the form widget to scroll area
        self.scroll_area.setWidget(form_widget)
        main_layout.addWidget(self.scroll_area)

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
        self.position_input.setText("QC Analyst")

        properties_data = [
            ("Color", "Blue", "Blue", "MBPI"),
            ("Specific Gravity", "1.00", "1.00 ± 0.20", "MBPI"),
            ("Durometer Hardness Shore \"A\"", "90.16", "90.0 ± 5.00", "ASTM D 2240"),
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
        if selected_record[3]:
            self.delivery_date.setDate(
                QDate(selected_record[3].year, selected_record[3].month, selected_record[3].day)
            )

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
        global current_coa_id
        current_coa_id = None
        self.default_values()
        self.code_input.clear()
        self.lot_number_input.clear()
        self.quantity_input.clear()
        self.delivery_receipt_input.clear()
        self.certified_by_name_input.clear()
        self.manufacturing_date_input.clear_value()
        self.btn_submit.setText("Submit")

    def on_submit_clicked(self, print_after=False):
        """Handle submit button click"""
        # Collect data from fields
        data = {
            'customer_name': self.customer_input.text(),
            'color_code': self.code_input.text(),
            'lot_number': self.lot_number_input.text(),
            'delivery_receipt_number': self.delivery_receipt_input.text(),
            'quantity_delivered': self.quantity_input.text(),
            'manufacturing_date': prod_date_format.dates_for_db(self.manufacturing_date_input.get_selected_dates()),
            'delivery_date': self.delivery_date.date().toString("yyyy-MM-dd"),
            'shelf_life': self.shelf_life_input.text(),
            'certified_by': self.certified_by_name_input.text(),
            'certification_date': self.date_input.date().toString("yyyy-MM-dd"),
            'product_name': self.product_name_input.text(),
            'position': self.position_input.text()
        }
        properties_data = self.get_properties_table_data()
        # Process the data (you can implement your own logic here)

        required_fields = {
            "Customer Name": data['customer_name'],
            "Color Code": data['color_code'],
            "Product Name": data['product_name'],
            "Manufacturing Date": data['manufacturing_date'],
            "Lot Number": data['lot_number'],
            "Delivery Receipt": data['delivery_receipt_number'],
            "Total Quantity": data['quantity_delivered'],
            "Certified By": data['certified_by'],
            "Shelf Life": data['shelf_life']
        }

        # Check if any required field is empty
        for field, value in required_fields.items():
            if not value:  # empty string
                window_alert.show_message(self, "Missing Input", f"Please fill in:  {field}", icon_type="warning")
                return  # stop processing

        # Check summary of analysis if no empty row
        if not any(any(cell for cell in row) for row in properties_data.values()):
            window_alert.show_message(self, "Missing Input", "Please fill in the Summary of Analysis table.",
                                      icon_type="warning")
            return

            # Validate certified_by against the list from the database
        if self.certified_by_name_input.text() not in self.certified_by_lists:
            window_alert.show_message(self, "Invalid Input", f"Certified By: '{self.certified_by_name_input.text()}' is not in the list.",
                                      icon_type="warning")
            return

        if print_after:
            returning_coa_id = db_con.save_pvc_free_coi(data, properties_data)
            self.open_packageworld_rowell_preview(returning_coa_id, "temp")
            self.scroll_area.verticalScrollBar().setValue(0)

            return

        try:
            global current_coa_id
            if current_coa_id is not None:  # Update existing COA
                db_con.update_pvc_free_coi(current_coa_id, data, properties_data)
                window_alert.show_message(self, "Success", f"Certificate of Analysis updated successfully!",
                                          icon_type="info")
                current_coa_id = None
            else:  # Insert new COA
                db_con.save_pvc_free_coi(data, properties_data)
                window_alert.show_message(self, "Success", f"Certificate of Analysis saved successfully!",
                                          icon_type="info")
                current_coa_id = None
            self.clear_form()
            self.scroll_area.verticalScrollBar().setValue(0)
        except Exception as e:
            window_alert.show_message(self, "Database Error", str(e), icon_type="critical")

    def load_coa_details(self, coa_id):

        try:
            self.delivery_receipt_input.blockSignals(True)
            field_result = db_con.get_single_coa_data(coa_id)
            properties_table_result = db_con.get_pvc_free_properties(coa_id)

            # === Populate inputs ===
            if field_result:
                self.customer_input.setText(str(field_result[1]))
                self.code_input.setText(str(field_result[2]))
                self.lot_number_input.setText(str(lot_format.normalize(field_result[3])))
                self.delivery_receipt_input.setText(str(field_result[5]))
                self.quantity_input.setText(str(field_result[6]))
                if field_result[7]:
                    self.delivery_date.setDate(
                        QDate(field_result[7].year, field_result[7].month, field_result[7].day)
                    )
                if field_result[8]:
                    self.manufacturing_date_input.display_value(prod_date_format.dates_for_display(str(field_result[8])))
                self.shelf_life_input.setText(str(field_result[12]))
                self.certified_by_name_input.setText(str(field_result[10]))
                if field_result[9]:
                    self.date_input.setDate(
                        QDate(field_result[9].year, field_result[9].month, field_result[9].day)
                    )
                    
            self.product_name_input.setText(str(properties_table_result[0][0]))
            self.position_input.setText(str(properties_table_result[0][1]))

            # === Populate properties table ===
            self.properties_table.setRowCount(0)
            self.properties_table.setRowCount(len(properties_table_result) - 1)
            for row_idx, (property_name, delivery, standard, method) in enumerate(properties_table_result[1:]):
                self.properties_table.setItem(row_idx, 0, QTableWidgetItem(property_name))
                self.properties_table.setItem(row_idx, 1, QTableWidgetItem(delivery))
                self.properties_table.setItem(row_idx, 2, QTableWidgetItem(standard))
                self.properties_table.setItem(row_idx, 3, QTableWidgetItem(method))

            self.adjust_table_height()
            self.btn_submit.setText("Update")
            self.btn_save_as_new.setVisible(True)
            self.delivery_receipt_input.blockSignals(False)

        except Exception as e:
            print(f"Load Rowell COI error: {e}")

    def rowell_save_as_new_clicked(self):
        global current_coa_id
        current_coa_id = None
        self.on_submit_clicked()

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

    def open_packageworld_rowell_preview(self, coa_id, filename):
        # If the widget already exists, close it first to avoid multiple instances

        try:
            if self.rowell_widget is not None:
                self.rowell_widget.close()
                self.rowell_widget.deleteLater()  # Good practice
            self.rowell_widget = FileRowell()
            self.rowell_widget.show_pdf_preview(coa_id, filename)
            self.rowell_widget.resize(900, 800)
            self.rowell_widget.show()
            self.rowell_widget.activateWindow()
            self.rowell_widget.raise_()
        except Exception as e:
            print(e)
