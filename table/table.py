from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidget, QTableView

from db import db_con
from utils import abs_path, lot_format


def load_msds_table(self):
    # Keep this as is since MSDS is still a QTableWidget
    self.msds_records_table.setRowCount(0)
    records = db_con.get_all_msds_data()
    if not records:
        self.msds_records_table.insertRow(0)
        no_data_item = self.create_readonly_item("No MSDS records found.", column_idx=0)
        self.msds_records_table.setItem(0, 0, no_data_item)
        self.msds_records_table.setSpan(0, 0, 1, self.msds_records_table.columnCount())
        return

    for row_idx, record in enumerate(records):
        msds_id, customer_name, _, product_code, creation_date = record[:5]
        revision_date_str = creation_date.strftime("%m-%d-%Y")
        display_text = f"{customer_name} {product_code} MSDS {revision_date_str}".upper()

        self.msds_records_table.insertRow(row_idx)
        self.msds_records_table.setItem(row_idx, 0, self.create_readonly_item(display_text, column_idx=0))
        self.msds_records_table.setItem(row_idx, 1,
                                        self.create_readonly_item(icon_path=abs_path.resource("img/view_icon.png"),
                                                                  selectable=False))
        self.msds_records_table.setItem(row_idx, 2,
                                        self.create_readonly_item(icon_path=abs_path.resource("img/edit_icon.png"),
                                                                  selectable=False))
        self.msds_records_table.setItem(row_idx, 3,
                                        self.create_readonly_item(icon_path=abs_path.resource("img/delete_icon.png"),
                                                                  selectable=False))
        self.msds_records_table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, msds_id)


def load_coa_table(self):
    """Refactored for QTableView and TableModel"""
    records = db_con.get_all_coa_data()
    processed_data = []

    if not records:
        # Pass an empty list to the model to clear it
        self.coa_model.set_data([])
        return

    for record in records:
        coa_id = record[0]
        customer_name = record[1]
        color_code = record[2]
        lot_number = lot_format.lot_for_filename(record[3])
        delivery_receipt_number = record[5]
        delivery_date_str = record[7].strftime("%m%d%y")

        display_text = f"{delivery_date_str} DRN{delivery_receipt_number} COA {customer_name} {color_code} {lot_number}".upper()

        # The Model expects: [Col 0 Text, Col 1 Placeholder, Col 2 Placeholder, Col 3 Placeholder, ID at index 4]
        processed_data.append([display_text, "", "", "", coa_id])

    # Send the whole list to the model at once
    self.coa_model.set_data(processed_data)


def load_rrf_table(self):
    """Refactored for QTableView and TableModel"""
    records = db_con.get_all_coa_data_rrf()
    processed_data = []

    if not records:
        self.coa_model.set_data([])
        return

    for record in records:
        coa_id = record[0]
        customer_name = record[1]
        color_code = record[2]
        lot_number = lot_format.lot_for_filename(record[3])
        rrf_number = record[5]
        delivery_date_str = record[7].strftime("%m%d%y")

        display_text = f"{delivery_date_str} RRF{rrf_number} COA {customer_name} {color_code} {lot_number}".upper()

        processed_data.append([display_text, "", "", "", coa_id])

    self.coa_model.set_data(processed_data)


def resize_columns(self, table, event):
    """Works for both QTableWidget and QTableView"""
    total_width = table.viewport().width()
    icon_col_width = 40

    # Number of columns (usually 4: Name, View, Edit, Delete)
    col_count = 4

    # Set icon columns
    for col in range(1, col_count):
        table.setColumnWidth(col, icon_col_width)

    # First column takes the rest
    remaining_width = total_width - (icon_col_width * (col_count - 1))
    if remaining_width > 0:
        table.setColumnWidth(0, remaining_width)


def search_msds(self, query):
    # QTableWidget style
    query = query.strip().lower()
    for row in range(self.msds_records_table.rowCount()):
        item = self.msds_records_table.item(row, 0)
        match = query in item.text().lower() if item else False
        self.msds_records_table.setRowHidden(row, not match)


def search_coa(self, query):
    """Use the Model's filter logic"""
    # col_index=0 means we are searching against the 'display_text' column
    self.coa_model.filter_data(query, col_index=0)


def search_coa_rrf(self, query):
    """Use the Model's filter logic"""
    self.coa_model.filter_data(query, col_index=0)