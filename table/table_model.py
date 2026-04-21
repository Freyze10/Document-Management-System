# table_model/model.py

from PyQt6.QtCore import Qt, QAbstractTableModel
from datetime import datetime

class TableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._all_data = data or []  # Backup for filtering
        self._data = data or []  # Current visible data
        self._headers = headers

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        # --- OPTION 3: HOVER TOOLTIP LOGIC ---
        if role == Qt.ItemDataRole.ToolTipRole:
            row = index.row()
            # If WIP No is at index 7, show it on hover
            if len(self._data[row]) > 7:
                wip_no = self._data[row][7]
                if wip_no and str(wip_no).strip() not in ("", "None", "0", "--"):
                    return f"WIP Number: {wip_no}"

        # Display Text
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            try:
                return self._data[index.row()][index.column()]
            except IndexError:
                return None
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            else:
                return str(section + 1)
        return None

    # --- SMART SORTING (Supports Dates and Numbers) ---
    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()

        def smart_sort_key(row):
            val = str(row[column])

            # 1. Try Audit Trail Timestamp (MM/DD/YYYY HH:MM:SS)
            try:
                return datetime.strptime(val, '%m/%d/%Y %H:%M:%S')
            except (ValueError, TypeError):
                pass

            # 2. Try Standard Date (MM/DD/YYYY)
            try:
                return datetime.strptime(val, '%m/%d/%Y')
            except (ValueError, TypeError):
                pass

            # 3. Try Numbers (so 10 comes after 2)
            try:
                clean_val = val.replace(',', '').replace('$', '')
                return float(clean_val)
            except (ValueError, TypeError):
                pass

            # 4. Fallback to lowercase string
            return val.lower()

        self._data.sort(
            key=smart_sort_key,
            reverse=(order == Qt.SortOrder.DescendingOrder)
        )
        self.layoutChanged.emit()

    def set_data(self, data):
        """Update the entire data and refresh the view"""
        self.beginResetModel()
        self._all_data = data if data is not None else []
        self._data = self._all_data[:]
        self.endResetModel()

    def filter_data(self, search_text, col_index=None):
        """Filter rows by search_text."""
        self.beginResetModel()
        if not search_text or not search_text.strip():
            self._data = self._all_data[:]
        else:
            kw = search_text.lower().strip()
            self._data = []
            for row in self._all_data:
                if col_index is not None:
                    match = col_index < len(row) and kw in str(row[col_index]).lower()
                else:
                    match = any(kw in str(cell).lower() for cell in row)
                if match:
                    self._data.append(row)
        self.endResetModel()

    def clear_data(self):
        """Clear all data"""
        self.beginResetModel()
        self._data = []
        self.endResetModel()