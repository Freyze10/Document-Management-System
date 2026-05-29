# table_model/model.py
from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QIcon
from datetime import datetime
from utils import abs_path


class TableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        # self._all_data is the master "source of truth"
        self._all_data = data if data is not None else []
        # self._data is what is currently visible (filtered or sorted)
        self._data = self._all_data[:]
        self._headers = headers
        self.hovered_row = -1
        self.hovered_col = -1

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    # --- ADD THIS METHOD FOR SEARCHING ---
    def filter_data(self, query, col_index=0):
        """Filters the table based on the search query."""
        self.beginResetModel()
        query = query.strip().lower()

        if not query:
            # If search is empty, restore all data
            self._data = self._all_data[:]
        else:
            # Filter the master list into the display list
            self._data = [
                row for row in self._all_data
                if query in str(row[col_index]).lower()
            ]
        self.endResetModel()

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
            if col == 0:
                return str(self._data[row][0])
            return None

        # UserRole: Return the ID (index 4 in your processed_data)
        if role == Qt.ItemDataRole.UserRole:
            return self._data[row][4] if len(self._data[row]) > 4 else None

        # DecorationRole: Icons
        if role == Qt.ItemDataRole.DecorationRole:
            is_hovered = (row == self.hovered_row and col == self.hovered_col)
            if col == 1:
                path = "img/hover_view_icon.png" if is_hovered else "img/view_icon.png"
                return QIcon(abs_path.resource(path))
            elif col == 2:
                path = "img/hover_edit_icon.png" if is_hovered else "img/edit_icon.png"
                return QIcon(abs_path.resource(path))
            elif col == 3:
                path = "img/hover_delete_icon.png" if is_hovered else "img/delete_icon.png"
                return QIcon(abs_path.resource(path))

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def set_data(self, data):
        """Updates the master data and the viewable data."""
        self.beginResetModel()
        self._all_data = data if data is not None else []
        self._data = self._all_data[:]  # Reset display data to match new master data
        self.endResetModel()

    def update_hover(self, row, col):
        self.hovered_row = row
        self.hovered_col = col
        self.dataChanged.emit(self.index(row, 1), self.index(row, 3))