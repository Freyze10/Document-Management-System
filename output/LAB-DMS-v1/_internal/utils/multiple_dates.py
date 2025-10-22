from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QDialog, QPushButton,
    QCalendarWidget, QLabel, QLineEdit, QHBoxLayout
)
from PyQt6.QtCore import QDate, Qt, QRect
from PyQt6.QtGui import QPalette, QColor, QPainter, QPen, QFont

# Enhanced custom stylesheet for better design with improved button readability
CALENDAR_STYLE = """
QCalendarWidget {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    font-size: 12px;
}

QCalendarWidget QAbstractItemView:enabled {
    selection-background-color: #66bb6a; /* Green for selected dates */
    selection-color: white;
    font-weight: bold;
}

QCalendarWidget QToolButton {
    color: #343a40;
    background-color: #f8f9fa;
    border: none;
    padding: 5px;
}

QCalendarWidget QToolButton:hover {
    background-color: #e9ecef;
}

QCalendarWidget QMenu {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
}

"""
OKBUTTON = """
QPushButton {
    background-color: #66bb6a;
    color: #ffffff; /* Ensure white text for contrast */
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 12px; /* Ensure readable font size */
    font-weight: bold; /* Make text stand out */
}

QPushButton:hover {
    background-color: #4caf50; /* Darker green on hover for better visibility */
    color: #ffffff; /* Maintain white text on hover */
}"""

# Custom Calendar Widget to handle multiple date selection and highlighting
class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_dates = set()
        self.setGridVisible(True)
        # Remove vertical header
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

    def paintCell(self, painter: QPainter, rect: QRect, date: QDate):
        super().paintCell(painter, rect, date)
        if date in self.selected_dates:
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.setBrush(QColor("#66bb6a"))
            circle_diameter = min(rect.width(), rect.height()) // 3
            circle_rect = QRect(
                rect.center().x() - circle_diameter // 2,
                rect.center().y() - circle_diameter // 2,
                circle_diameter,
                circle_diameter
            )
            painter.drawEllipse(circle_rect)
            painter.restore()

    def toggle_date(self, date: QDate):
        if date in self.selected_dates:
            self.selected_dates.remove(date)
        else:
            self.selected_dates.add(date)
        self.updateCell(date)  # Update only the changed cell

    def get_selected_dates(self):
        return sorted(self.selected_dates)

    def set_selected_dates(self, dates):
        self.selected_dates = set(dates)
        self.update()  # Redraw the entire calendar

class MultiDateCalendar(QDialog):
    def __init__(self, parent=None, preselected_dates=None):
        super().__init__(parent)
        self.setWindowTitle("Select Multiple Dates")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        self.calendar = CustomCalendarWidget(self)
        self.calendar.setStyleSheet(CALENDAR_STYLE)
        self.calendar.clicked.connect(self.toggle_date_selection)

        self.label = QLabel("Click dates to select or unselect (green circle indicates selection).")
        self.label.setStyleSheet("color: #343a40; font-size: 12px;")
        self.ok_button = QPushButton("OK")
        self.ok_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Explicit font settings
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setStyleSheet(OKBUTTON)

        layout.addWidget(self.calendar)
        layout.addWidget(self.label)
        layout.addWidget(self.ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Set preselected dates
        if preselected_dates:
            self.calendar.set_selected_dates(preselected_dates)

    def toggle_date_selection(self, date: QDate):
        self.calendar.toggle_date(date)

    def get_selected_dates(self):
        return self.calendar.get_selected_dates()

class MultiDateInput(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Remove the label and use only the QLineEdit
        self.multi_date_input = QLineEdit()
        self.multi_date_input.setPlaceholderText("Click to select multiple dates")
        self.multi_date_input.setStyleSheet("""
            font-size: 12px;
            padding: 6px 8px;
            border: 1px solid #ced4da; /* Lighter, more neutral border */
            border-radius: 6px; /* Slightly less rounded for a crisp look */
            background-color: #ffffff;
            min-height: 28px; /* Consistent height */
            selection-background-color: #aed6f1;
        """)
        self.multi_date_input.mousePressEvent = self.open_calendar_dialog
        layout.addWidget(self.multi_date_input)

        self.selected_dates = []

    def open_calendar_dialog(self, event):
        dialog = MultiDateCalendar(self, preselected_dates=self.selected_dates)
        if dialog.exec():
            self.selected_dates = dialog.get_selected_dates()
            text = ", ".join(d.toString("MM/dd/yyyy") for d in self.selected_dates)
            self.multi_date_input.setText(text)

    def get_selected_dates(self):
        """Return the selected dates as QDate objects."""
        return self.multi_date_input.text()

    def clear_value(self):
        self.multi_date_input.clear()
        self.selected_dates = []

    def display_value(self, value):
        self.multi_date_input.setText(value)


# if __name__ == "__main__":
#     app = QApplication([])
#     app.setStyleSheet(CALENDAR_STYLE)  # Apply global stylesheet
#     window = MultiDateInput()
#     window.setWindowTitle("Multi-Date Picker Example")
#     window.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px;")
#     window.resize(400, 150)
#     window.show()
#     app.exec()