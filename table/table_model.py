# table_model/model.py
from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QIcon
from datetime import datetime
from utils import abs_path


class TableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._all_data = data or []
        self._data = data or []
        self._headers = headers
        # Track hover state for icons
        self.hovered_row = -1
        self.hovered_col = -1

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        # ToolTip Logic
        if role == Qt.ItemDataRole.ToolTipRole:
            if len(self._data[row]) > 7:
                wip_no = self._data[row][7]
                if wip_no and str(wip_no).strip() not in ("", "None", "0", "--"):
                    return f"WIP Number: {wip_no}"

        # Display Text
        if role == Qt.ItemDataRole.DisplayRole:
            # We only show text in column 0 (The Name)
            if col == 0:
                return str(self._data[row][0])
            return None

        # UserRole: Return the ID (stored in the hidden part of the row list, e.g., index 0)
        if role == Qt.ItemDataRole.UserRole:
            # Assuming coa_id is stored in the data list for that row
            # Usually, row data looks like [id, name, ...] or similar
            return self._data[row][4] if len(self._data[row]) > 4 else None

        # DecorationRole: This is how we show ICONS in QTableView
        if role == Qt.ItemDataRole.DecorationRole:
            is_hovered = (row == self.hovered_row and col == self.hovered_col)

            if col == 1:  # View
                path = "img/hover_view_icon.png" if is_hovered else "img/view_icon.png"
                return QIcon(abs_path.resource(path))
            elif col == 2:  # Edit
                path = "img/hover_edit_icon.png" if is_hovered else "img/edit_icon.png"
                return QIcon(abs_path.resource(path))
            elif col == 3:  # Delete
                path = "img/hover_delete_icon.png" if is_hovered else "img/delete_icon.png"
                return QIcon(abs_path.resource(path))

        # Alignment
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
        return None

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()

        def smart_sort_key(row):
            val = str(row[column])
            try:
                return datetime.strptime(val, '%m/%d/%Y %H:%M:%S')
            except:
                pass
            try:
                return datetime.strptime(val, '%m/%d/%Y')
            except:
                pass
            try:
                clean_val = val.replace(',', '').replace('$', '')
                return float(clean_val)
            except:
                pass
            return val.lower()

        self._data.sort(key=smart_sort_key, reverse=(order == Qt.SortOrder.DescendingOrder))
        self.layoutChanged.emit()

    def set_data(self, data):
        self.beginResetModel()
        self._all_data = data if data is not None else []
        self._data = self._all_data[:]
        self.endResetModel()

    def update_hover(self, row, col):
        """Custom method to trigger icon updates on hover"""
        self.hovered_row = row
        self.hovered_col = col
        # Notify view that the data in these columns changed to redraw icons
        self.dataChanged.emit(self.index(row, 1), self.index(row, 3))