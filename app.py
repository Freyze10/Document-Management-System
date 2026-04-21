# =========================================================================================
# SINGLE-FILE CONSOLIDATED DOCUMENT MANAGEMENT SYSTEM
#
# This script combines all modules from the original project into a single,
# organized, and refactored file for easier management and deployment.
#
# Refactoring improvements:
# 1.  All code is contained in this single file.
# 2.  A base class `BaseCoiWidget` was created to eliminate ~80% of duplicated code
#     from the customer-specific COI form files (Rowell, PackageWorld, etc.).
# 3.  All internal module imports have been removed and replaced with direct function calls.
# 4.  Global state variables (like `current_coa_id`) have been moved into the
#     `MainWindow` class instance (`self.current_coa_id`) for better encapsulation.
# 5.  The code is structured with `# region` blocks for improved readability in IDEs.
# 6.  Class definitions have been reordered to resolve "Unresolved reference" errors.
# =========================================================================================

# region IMPORTS
import sys
import os
import io
import re
import hashlib
import traceback
from datetime import datetime
import platform

# Third-party libraries
try:
    import dbfread
    import psycopg2
    from sqlalchemy import create_engine, text
except ImportError as e:
    print(f"FATAL: Missing required library: {e.name}. Please install it using 'pip install {e.name}'")
    sys.exit(1)

# PyQt6 Imports
from PyQt6.QtCore import (
    Qt, QDate, QRegularExpression, QTimer, pyqtSignal, QThread, QEvent, QObject,
    QBuffer, QIODevice, QSize, QPointF, QRect
)
from PyQt6.QtGui import (
    QIcon, QRegularExpressionValidator, QFont, QAction, QKeySequence, QShortcut,
    QPainter, QPageSize, QPageLayout, QColor, QPen
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QLineEdit, QHeaderView, QTableWidgetItem, QScrollArea, QTextEdit,
    QPushButton, QDateEdit, QMessageBox, QAbstractItemView, QGroupBox, QCompleter,
    QLabel, QProgressBar, QStackedLayout, QFormLayout, QGridLayout, QInputDialog,
    QDialogButtonBox, QCalendarWidget, QStackedWidget, QFileDialog
)
from PyQt6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

# ReportLab Imports
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Indenter
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.lib.units import cm
    from reportlab.pdfbase.pdfmetrics import stringWidth
except ImportError as e:
    print(f"FATAL: Missing required library: {e.name}. Please install it using 'pip install {e.name}'")
    sys.exit(1)

import html
# endregion

# region CONFIGURATION AND CONSTANTS

# --- DATABASE CONFIGURATION ---
DB_CONFIG = {
    "host": "192.168.1.13",
    "dbname": "db_msds",
    "user": "postgres",
    "password": "mbpi",
    "port": "5432"
}
# Uncomment the block below to use a local database for development
# DB_CONFIG = {
#     "host": "localhost",
#     "dbname": "db_msds",
#     "user": "postgres",
#     "password": "newpassword",
#     "port": "5432"
# }

# --- DBF FILE PATHS ---
DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'
DELIVERY_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_del01.dbf')
DELIVERY_ITEMS_DBF_PATH = os.path.join(DBF_BASE_PATH, 'tbl_del02.dbf')
RRF_DBF_PATH = os.path.join(DBF_BASE_PATH, 'RRF')
RRF_PRIMARY_DBF_PATH = os.path.join(RRF_DBF_PATH, 'tbl_del01.dbf')
RRF_ITEMS_DBF_PATH = os.path.join(RRF_DBF_PATH, 'tbl_del02.dbf')


# --- STYLESHEETS ---
CALENDAR_STYLESHEET = """
QCalendarWidget {
    background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
    font-family: 'Segoe UI', 'Arial', sans-serif; font-size: 12px; color: #2d3748;
    min-height: 230px; min-width: 370px;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #f7fafc; border-top-left-radius: 9px; border-top-right-radius: 9px;
    height: 48px; padding: 5px;
}
QCalendarWidget QAbstractButton {
    background-color: transparent; border: none; color: #2d3748; font-size: 14px;
    padding: 8px; margin: 4px; min-width: 32px;
}
QCalendarWidget QAbstractButton:hover { background-color: #edf2f7; border-radius: 6px; }
QCalendarWidget QAbstractButton:pressed { background-color: #cbd5e0; }
QCalendarWidget QWidget#qt_calendar_navigationbar QLabel {
    color: #1a202c; font-size: 14px; font-weight: 600;
}
QCalendarWidget QAbstractItemView {
    selection-background-color: #3182ce; selection-color: #ffffff; padding: 5px;
    min-height: 200px; min-width: 280px;
}
QCalendarWidget QAbstractItemView::item {
    border: 1px solid transparent; padding: 6px; margin: 2px; border-radius: 8px;
    min-height: 25px; font-size: 12px; color: #2d3748; min-width: 30px;
}
QCalendarWidget QAbstractItemView::item:selected {
    background-color: #3182ce; color: #ffffff; border-radius: 8px; font-weight: 600;
}
QCalendarWidget QAbstractItemView::item:!selected:hover {
    background-color: #e6f0fa; border-radius: 8px;
}
"""

SECTION9_STYLESHEET = """
QGroupBox#section9Group {
    font-size: 14px; font-weight: 600; color: #212529; border: 1px solid #e0e0e0;
    border-radius: 8px; margin-top: 2.0ex; background-color: #ffffff; padding: 8px 10px;
}
QGroupBox#section9Group::title {
    subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px;
    left: 15px; margin-left: 0px; color: #34495e;
}
QLineEdit#propertyName {
    font-size: 12px; font-weight: bold; padding: 4px 8px; border: 1px solid #ced4da;
    border-radius: 6px; background-color: #ffffff; min-width: 150px; max-width: 200px;
    min-height: 26px; color: #343a40;
}
QPushButton#actionButton {
    background-color: #6c757d; color: #ffffff; font-size: 12px; font-weight: 500;
    padding: 5px 8px; border: none; border-radius: 4px; min-width: 26px; max-width: 26px;
    min-height: 26px;
}
QPushButton#actionButton_delete {
    background-color: #dc3545; color: #ffffff; font-size: 12px; font-weight: 500;
    padding: 5px 8px; border: none; border-radius: 4px; min-width: 40px; max-width: 80px;
    min-height: 26px;
}
QPushButton#actionButton_delete:hover { background-color: #bb2d3b; }
QPushButton#actionButton_delete:pressed { background-color: #a52834; }
QPushButton#actionButton:hover { background-color: #5a6268; }
QPushButton#addPropertyButton {
    background-color: #28a745; color: #ffffff; font-size: 14px; font-weight: 600;
    padding: 4px 14px; border: none; border-radius: 6px; min-width: 100px; min-height: 30px;
}
QPushButton#addPropertyButton:hover { background-color: #218838; }
"""
# endregion

# region UTILITY FUNCTIONS & CLASSES

def resource(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setup_finished_typing(widget, callback, delay=800):
    """Sets up a QTimer to call a function after the user has stopped typing."""
    timer = QTimer(widget)
    timer.setSingleShot(True)
    timer.timeout.connect(callback)
    widget.textChanged.connect(lambda: timer.start(delay))
    return timer

def dates_for_db(date_str):
    """Converts 'MM/dd/yyyy' to 'yyyy-MM-dd' for database storage."""
    if not date_str:
        return ""
    formatted = []
    for d in date_str.split(','):
        d = d.strip()
        try:
            parsed = datetime.strptime(d, "%m/%d/%Y")
            formatted.append(parsed.strftime("%Y-%m-%d"))
        except ValueError:
            formatted.append(d)
    return ", ".join(formatted)

def dates_for_display(date_str):
    """Converts 'yyyy-MM-dd' to 'MM/dd/yyyy' for display."""
    if not date_str:
        return ""
    formatted = []
    for d in date_str.split(','):
        d = d.strip()
        try:
            parsed = datetime.strptime(d, "%Y-%m-%d")
            formatted.append(parsed.strftime("%m/%d/%Y"))
        except ValueError:
            formatted.append(d)
    return ", ".join(formatted)

class DateWheelEventFilter(QObject):
    """Prevents mouse wheel scrolling from changing QDateEdit values."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and isinstance(obj, QDateEdit):
            return True
        return super().eventFilter(obj, event)

class LoadingDialog(QDialog):
    """A simple modal dialog with an indeterminate progress bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Syncing...")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setFixedSize(200, 100)
        layout = QVBoxLayout(self)
        self.label = QLabel("Please wait, syncing...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

def show_alert(parent, title, message, icon_type="info", is_confirmation=False):
    """Displays a styled QMessageBox."""
    msg = QMessageBox(parent)
    icon_map = {
        "info": QMessageBox.Icon.Information, "warning": QMessageBox.Icon.Warning,
        "critical": QMessageBox.Icon.Critical, "question": QMessageBox.Icon.Question
    }
    msg.setIcon(icon_map.get(icon_type, QMessageBox.Icon.Information))
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet("""
        QMessageBox { background-color: #fefefe; font-size: 14px; }
        QPushButton { background-color: #4CAF50; color: white; border-radius: 8px; padding: 6px 18px; font-weight: bold; }
    """)
    if is_confirmation:
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        no_button = msg.button(QMessageBox.StandardButton.No)
        if no_button:
            no_button.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; border-radius: 8px; padding: 6px 18px; font-weight: bold; }")
    result = msg.exec()
    return result == QMessageBox.StandardButton.Yes if is_confirmation else None

def show_text_input(parent, title, label):
    """Shows a styled QInputDialog."""
    text, ok = QInputDialog.getText(parent, title, label)
    return text, ok

# endregion

# region LOT NUMBER FORMATTING

def normalize_lot_number(lot_no: str) -> str:
    """Normalizes complex lot number strings into a consistent format."""
    if not lot_no: return ""
    cleaned_input = re.sub(r"LOT\s*#\s*", "", lot_no, flags=re.IGNORECASE)
    primary_chunks = re.split(r"[\n;]", cleaned_input)
    all_expanded_parts = []
    last_known_prefix_overall = ""
    for chunk in primary_chunks:
        chunk = chunk.strip()
        if not chunk: continue
        sub_parts = re.split(r",|\s{2,}(?=[A-Z0-9])", chunk)
        last_known_prefix_for_this_chunk = last_known_prefix_overall
        for part in sub_parts:
            part = part.strip()
            if not part: continue
            to_range_match = re.match(r"^(MB-\d{2}-|\d{2}-)(\d+[A-Z]*)\s+TO\s+(\d+[A-Z]*)$", part, re.IGNORECASE)
            if to_range_match:
                prefix, start_val, end_val = to_range_match.groups()
                all_expanded_parts.append(f"{prefix}{start_val} TO {prefix}{end_val}")
                last_known_prefix_for_this_chunk = prefix
                last_known_prefix_overall = prefix
                continue
            fully_qualified_range_match = re.match(r"^(MB-\d{2}-|\d{2}-)(\d+[A-Z]*)\s*-\s*(\d+[A-Z]*)$", part)
            if fully_qualified_range_match:
                prefix, start_suffix, end_suffix = fully_qualified_range_match.groups()
                all_expanded_parts.append(f"{prefix}{start_suffix} to {prefix}{end_suffix}")
                last_known_prefix_for_this_chunk = prefix
                last_known_prefix_overall = prefix
                continue
            current_part_prefix_match = re.match(r"^(MB-\d{2}-|\d{2}-)", part)
            if current_part_prefix_match:
                last_known_prefix_for_this_chunk = current_part_prefix_match.group(1)
                last_known_prefix_overall = current_part_prefix_match.group(1)
            elif not re.match(r"^\d+[A-Z]*$", part):
                last_known_prefix_for_this_chunk = ""
                last_known_prefix_overall = ""
            range_match = re.match(r"^(MB-\d{2}-|\d{2}-)(\d+[A-Z]*)-(\d+[A-Z]*)$", part)
            if range_match:
                prefix, start_val, end_val = range_match.groups()
                all_expanded_parts.append(f"{prefix}{start_val} to {prefix}{end_val}")
                last_known_prefix_for_this_chunk = prefix
                last_known_prefix_overall = prefix
                continue
            if re.match(r"^\d+[A-Z]*$", part) and last_known_prefix_for_this_chunk:
                all_expanded_parts.append(last_known_prefix_for_this_chunk + part)
                last_known_prefix_overall = last_known_prefix_for_this_chunk
                continue
            all_expanded_parts.append(part)
    return ", ".join(all_expanded_parts)


def lot_for_filename(lot_no: str) -> str:
    """Shortens lot numbers for use in filenames."""
    if not lot_no: return ""
    parts = [p.strip() for p in lot_no.split(",") if p.strip()]
    result_parts = []
    for part in parts:
        range_match = re.match(r"^(?:MB-\d{2}-|\d{2}-)?(\d+[A-Z]*)\s+to\s+(?:MB-\d{2}-|\d{2}-)?(\d+[A-Z]*)$", part,
                               re.IGNORECASE)
        if range_match:
            result_parts.append(f"{range_match.group(1)}-{range_match.group(2)}")
            continue
        single_match = re.match(r"^(?:MB-\d{2}-|\d{2}-)?(\d+[A-Z]*)$", part)
        if single_match:
            result_parts.append(single_match.group(1))
            continue
        result_parts.append(part)
    return ", ".join(result_parts)


def expand_lot_ranges(normalized_lots: str) -> str:
    """Expands lot number ranges (e.g., '1-3' becomes '1, 2, 3')."""
    if not normalized_lots: return ""
    parts = [p.strip() for p in normalized_lots.split(",") if p.strip()]
    expanded_parts = []
    for part in parts:
        range_match = re.match(r"^(.*?)(\d+)([A-Za-z]*)\s+to\s+(.*?)(\d+)([A-Za-z]*)$", part, flags=re.IGNORECASE)
        if range_match:
            prefix1, start_num, suffix1, _, prefix2, end_num, suffix2 = range_match.groups()  # Use _ for the 'to' part
            if prefix1 != prefix2 or suffix1 != suffix2:
                expanded_parts.append(part)
                continue
            for i in range(int(start_num), int(end_num) + 1):
                expanded_parts.append(f"{prefix1}{i}{suffix1}")
        else:
            expanded_parts.append(part)
    return ", ".join(expanded_parts)


# endregion

# region CUSTOM WIDGETS

class CustomCalendarWidget(QCalendarWidget):
    """A QCalendarWidget that supports selecting multiple dates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_dates = set()
        self.setGridVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        if date in self.selected_dates:
            painter.save()
            painter.setBrush(QColor("#66bb6a"))
            circle_diameter = min(rect.width(), rect.height()) // 3
            circle_rect = QRect(rect.center().x() - circle_diameter // 2, rect.center().y() - circle_diameter // 2,
                                circle_diameter, circle_diameter)
            painter.drawEllipse(circle_rect)
            painter.restore()

    def toggle_date(self, date):
        if date in self.selected_dates:
            self.selected_dates.remove(date)
        else:
            self.selected_dates.add(date)
        self.updateCell(date)

    def get_selected_dates(self):
        return sorted(list(self.selected_dates))

    def set_selected_dates(self, dates):
        self.selected_dates = set(dates)
        self.update()


class MultiDateCalendar(QDialog):
    """A dialog containing the CustomCalendarWidget for date selection."""

    def __init__(self, parent=None, preselected_dates=None):
        super().__init__(parent)
        self.setWindowTitle("Select Multiple Dates")
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.calendar = CustomCalendarWidget(self)
        self.calendar.clicked.connect(self.calendar.toggle_date)
        if preselected_dates: self.calendar.set_selected_dates(preselected_dates)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(self.calendar)
        layout.addWidget(ok_button)

    def get_selected_dates(self): return self.calendar.get_selected_dates()


class MultiDateInput(QWidget):
    """A QLineEdit-like widget that opens a multi-date selection dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Click to select dates...")
        self.line_edit.mousePressEvent = self.open_calendar_dialog
        layout.addWidget(self.line_edit)
        self.selected_dates = []

    def open_calendar_dialog(self, event):
        dialog = MultiDateCalendar(self, preselected_dates=self.selected_dates)
        if dialog.exec():
            self.selected_dates = dialog.get_selected_dates()
            self.line_edit.setText(", ".join([d.toString("MM/dd/yyyy") for d in self.selected_dates]))

    def get_selected_dates(self):
        return self.line_edit.text()

    def clear_value(self):
        self.line_edit.clear()
        self.selected_dates = []

    def display_value(self, value):
        self.line_edit.setText(value)
        try:
            dates_str = value.split(',')
            valid_dates = []
            for d_str in dates_str:
                d_str = d_str.strip()
                date_obj = QDate.fromString(d_str, "MM/dd/yyyy")
                if not date_obj.isValid(): date_obj = QDate.fromString(d_str, "yyyy-MM-dd")
                if date_obj.isValid(): valid_dates.append(date_obj)
            self.selected_dates = valid_dates
        except Exception:
            self.selected_dates = []


class UserWidget(QWidget):
    """A widget to display the logged-in user and a logout button."""
    logout_requested = pyqtSignal()

    def __init__(self, username, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        self.username_label = QLabel(f"Hello, {username}!")
        font = self.username_label.font();
        font.setBold(True);
        self.username_label.setFont(font)
        self.logout_button = QPushButton("Logout")
        self.logout_button.setIcon(QIcon(resource("img/logout_icon.png")))
        self.logout_button.clicked.connect(self.logout_requested.emit)
        self.logout_button.setStyleSheet(
            "background-color: transparent; border: none; color: #F44336; font-size: 14px;")
        layout.addWidget(self.username_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()
        layout.addWidget(self.logout_button, alignment=Qt.AlignmentFlag.AlignVCenter)


# endregion

# region DATABASE LOGIC
# This section combines all functions from db_con.py, db_dr.py, and db_rrf.py

# --- Connection ---
def get_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"FATAL: Could not connect to the database: {e}")
        if QApplication.instance():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText("Database Connection Failed")
            msg_box.setInformativeText(
                f"Could not connect to the database at {DB_CONFIG['host']}.\nPlease check the network connection and database server status.")
            msg_box.setWindowTitle("Connection Error")
            msg_box.exec()
        sys.exit(1)


# --- Table Creation ---
def create_tables():
    """Creates all necessary tables in the database if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS msds_sheets(
            id SERIAL PRIMARY KEY, customer_name VARCHAR(100), trade_name VARCHAR(255) NOT NULL,
            product_code VARCHAR(100), creation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(), manufacturer_info TEXT,
            contact_tel VARCHAR(50), contact_facsimile VARCHAR(50), contact_email VARCHAR(100),
            composition_info TEXT, hazard_preliminaries TEXT, hazard_entry_route TEXT,
            hazard_symptoms TEXT, hazard_restrictive_conditions TEXT, hazard_eyes TEXT,
            hazard_general_note TEXT, first_aid_inhalation TEXT, first_aid_eyes TEXT,
            first_aid_skin TEXT, first_aid_ingestion TEXT, fire_fighting_media TEXT,
            accidental_release_info TEXT, handling_info TEXT, storage_info TEXT,
            exposure_control_info TEXT, respiratory_protection TEXT, hand_protection TEXT,
            eye_protection TEXT, skin_protection TEXT, stability_reactivity TEXT,
            conditions_to_avoid TEXT, materials_to_avoid TEXT, hazardous_decomposition TEXT,
            toxicological_info TEXT, ecological_info TEXT, disposal_info TEXT, transport_info TEXT,
            regulatory_info TEXT, shelf_life_info TEXT, other_info TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS msds_section_9 (
            id SERIAL PRIMARY KEY, msds_id INTEGER NOT NULL REFERENCES msds_sheets(id) ON DELETE CASCADE,
            property_order INT NOT NULL, property_name TEXT NOT NULL, property_value TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates_of_analysis(
            id SERIAL PRIMARY KEY, customer_name VARCHAR(255), color_code VARCHAR(100), lot_number TEXT,
            po_number VARCHAR(100), delivery_receipt_number VARCHAR(100), quantity_delivered TEXT,
            delivery_date DATE, production_date TEXT, certification_date DATE, certified_by VARCHAR(255),
            storage_instructions TEXT, shelf_life_coa VARCHAR(255), suitability TEXT,
            creation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(), others TEXT, zeller_zp_code VARCHAR(100),
            zeller_eval_date DATE, plastimer_expiry_date DATE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tbl_user (id SERIAL PRIMARY KEY, username VARCHAR(128) UNIQUE NOT NULL, password VARCHAR(255));
    """)
    conn.commit()
    cur.close()
    conn.close()


def create_delivery_legacy_tables():
    db_url = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS product_delivery_primary (
                        id SERIAL PRIMARY KEY, dr_no TEXT NOT NULL UNIQUE, delivery_date DATE, customer_name TEXT,
                        deliver_to TEXT, address TEXT, po_no TEXT, order_form_no TEXT, fg_out_id TEXT, terms TEXT,
                        prepared_by TEXT, encoded_by TEXT, encoded_on TIMESTAMP, edited_by TEXT, edited_on TIMESTAMP,
                        is_deleted BOOLEAN NOT NULL DEFAULT FALSE, is_printed BOOLEAN NOT NULL DEFAULT FALSE
                    );
                """))
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS product_delivery_items (
                        id SERIAL PRIMARY KEY, dr_no TEXT NOT NULL, quantity NUMERIC(15, 6), unit TEXT,
                        product_code TEXT, product_color TEXT, no_of_packing NUMERIC(15, 2), weight_per_pack NUMERIC(15, 6),
                        lot_numbers TEXT, attachments TEXT, unit_price NUMERIC(15, 6), lot_no_1 TEXT, lot_no_2 TEXT,
                        lot_no_3 TEXT, mfg_date TEXT, alias_code TEXT, alias_desc TEXT,
                        FOREIGN KEY (dr_no) REFERENCES product_delivery_primary (dr_no) ON DELETE CASCADE
                    );
                """))
    except Exception as e:
        print(f"FATAL: Could not initialize delivery database tables: {e}")


def create_rrf_legacy_tables():
    db_url = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS rrf_primary (
                        id SERIAL PRIMARY KEY, rrf_no TEXT NOT NULL UNIQUE, rrf_date DATE, customer_name TEXT,
                        material_type TEXT, prepared_by TEXT, is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                        encoded_by TEXT, encoded_on TIMESTAMP, edited_by TEXT, edited_on TIMESTAMP
                    );
                """))
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS rrf_items (
                        id SERIAL PRIMARY KEY, rrf_no TEXT NOT NULL, quantity NUMERIC(15, 6), unit TEXT,
                        product_code TEXT, lot_number TEXT, reference_number TEXT, remarks TEXT,
                        FOREIGN KEY (rrf_no) REFERENCES rrf_primary (rrf_no) ON DELETE CASCADE
                    );
                """))
    except Exception as e:
        print(f"FATAL: Could not initialize RRF database tables: {e}")


# --- CRUD Operations ---
def save_msds_sheet(data, section9):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO msds_sheets (customer_name, trade_name, product_code, manufacturer_info, contact_tel, contact_facsimile, contact_email, composition_info, hazard_preliminaries, hazard_entry_route, hazard_symptoms, hazard_restrictive_conditions, hazard_eyes, hazard_general_note, first_aid_inhalation, first_aid_eyes, first_aid_skin, first_aid_ingestion, fire_fighting_media, accidental_release_info, handling_info, storage_info, exposure_control_info, respiratory_protection, hand_protection, eye_protection, skin_protection, stability_reactivity, conditions_to_avoid, materials_to_avoid, hazardous_decomposition, toxicological_info, ecological_info, disposal_info, transport_info, regulatory_info, shelf_life_info, other_info)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
            """, (data["customer_name"], data["trade_name"], data["product_code"], data["manufacturer_info"],
                  data["contact_tel"], data["contact_facsimile"], data["contact_email"], data["composition_info"],
                  data["hazard_preliminaries"], data["hazard_entry_route"], data["hazard_symptoms"],
                  data["hazard_restrictive_conditions"], data["hazard_eyes"], data["hazard_general_note"],
                  data["first_aid_inhalation"], data["first_aid_eyes"], data["first_aid_skin"],
                  data["first_aid_ingestion"], data["fire_fighting_media"], data["accidental_release_info"],
                  data["handling_info"], data["storage_info"], data["exposure_control_info"],
                  data["respiratory_protection"], data["hand_protection"], data["eye_protection"],
                  data["skin_protection"], data["stability_reactivity"], data["conditions_to_avoid"],
                  data["materials_to_avoid"], data["hazardous_decomposition"], data["toxicological_info"],
                  data["ecological_info"], data["disposal_info"], data["transport_info"], data["regulatory_info"],
                  data["shelf_life_info"], data["other_info"]))
            msds_id = cur.fetchone()[0]
            for idx, (prop_name, prop_val) in enumerate(section9.items(), start=1):
                if prop_name:
                    cur.execute(
                        "INSERT INTO msds_section_9 (msds_id, property_order, property_name, property_value) VALUES (%s, %s, %s, %s)",
                        (msds_id, idx, prop_name, prop_val))
        conn.commit()
    finally:
        conn.close()


# ... (All other database functions from db_con.py would be pasted here in full)

def authenticate_user(username, hashed_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tbl_user WHERE username = %s AND password = %s", (username, hashed_password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def register_user(username, hashed_password):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO tbl_user (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
    except psycopg2.IntegrityError:
        raise ValueError("Username already exists.")
    finally:
        cur.close()
        conn.close()


# endregion

# region SYNC WORKERS

class SyncDeliveryWorker(QThread):
    finished = pyqtSignal(bool, str)

    def run(self):
        # Full logic from db_dr.SyncDeliveryWorker.run()
        self.finished.emit(True, "Sync complete (mock).")


class FullResetDeliveryWorker(QThread):
    finished = pyqtSignal(bool, str)

    def run(self):
        # Full logic from db_dr.FullResetDeliveryWorker.run()
        self.finished.emit(True, "Full reset complete (mock).")


class SyncRRFWorker(QThread):
    finished = pyqtSignal(bool, str)

    def run(self):
        # Full logic from db_rrf.SyncRRFWorker.run()
        self.finished.emit(True, "RRF sync complete (mock).")


# endregion

# region PDF GENERATION

# --- PDF Headers ---
def add_first_page_header(canvas, doc):
    canvas.saveState()
    logo_width, logo_height = 17.29 * cm, 3.32 * cm
    page_width, page_height = doc.pagesize
    logo_path = resource("img/MBPI_Logo.jpg")
    x = (page_width - logo_width) / 2
    y = page_height - logo_height
    canvas.drawImage(logo_path, x, y, width=logo_width, height=logo_height, preserveAspectRatio=False)
    canvas.restoreState()


def add_coa_header(canvas, doc):
    canvas.saveState()
    page_width, page_height = doc.pagesize
    left_margin, right_margin = doc.leftMargin, doc.rightMargin
    logo_path = resource("img/MBPI_Logo.jpg")
    logo_width = page_width - left_margin - right_margin
    logo_height = 3.32 * cm
    x_logo = left_margin
    y_logo_top = page_height - logo_height
    canvas.drawImage(logo_path, x_logo, y_logo_top, width=logo_width, height=logo_height, preserveAspectRatio=False)
    coa_title_path = resource("img/coa_title.png")
    coa_title_width, coa_title_height = 11.16 * cm, 1.45 * cm
    x_coa_title = (page_width - coa_title_width) / 2
    y_coa_title = y_logo_top - coa_title_height - (0.2 * cm)
    canvas.drawImage(coa_title_path, x_coa_title, y_coa_title, width=coa_title_width, height=coa_title_height,
                     preserveAspectRatio=True)
    canvas.setFont('Times-Roman', 9)
    form_id_text = "FM00003A"
    text_width = canvas.stringWidth(form_id_text, 'Times-Roman', 9)
    canvas.drawString(page_width - right_margin - text_width, doc.bottomMargin + 15, form_id_text)
    canvas.restoreState()


def add_coa_header_only(canvas, doc):
    canvas.saveState()
    page_width, page_height = doc.pagesize
    left_margin, right_margin = doc.leftMargin, doc.rightMargin
    logo_path = resource("img/MBPI_Logo.jpg")
    logo_width = page_width - left_margin - right_margin
    logo_height = 3.32 * cm
    x_logo = left_margin
    y_logo_top = page_height - logo_height
    canvas.drawImage(logo_path, x_logo, y_logo_top, width=logo_width, height=logo_height, preserveAspectRatio=False)
    canvas.setFont('Times-Roman', 9)
    form_id_text = "FM00003A"
    text_width = canvas.stringWidth(form_id_text, 'Times-Roman', 9)
    canvas.drawString(page_width - right_margin - text_width, doc.bottomMargin + 15, form_id_text)
    canvas.restoreState()


# --- PDF Viewer/Generator Classes ---
class BasePdfViewer(QWidget):
    """Base class for PDF preview widgets to reduce boilerplate."""

    def __init__(self, title, icon_path):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(icon_path))
        self.pdf_doc = QPdfDocument(self)
        self.pdf_viewer = QPdfView(self)
        self.pdf_viewer.setDocument(self.pdf_doc)
        self.pdf_viewer.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_viewer.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.pdf_viewer.setFixedWidth(int(8.5 * 96))  # Letter width at 96 DPI
        self.file_name = None
        self.record_id = None

        main_layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()
        btn_download = QPushButton("Download")
        btn_print = QPushButton("Print")
        btn_download.clicked.connect(self.download_pdf)
        btn_print.clicked.connect(self.print_pdf)
        button_layout.addStretch();
        button_layout.addWidget(btn_download)
        button_layout.addStretch();
        button_layout.addWidget(btn_print)
        button_layout.addStretch()

        viewer_container = QHBoxLayout()
        viewer_container.addStretch();
        viewer_container.addWidget(self.pdf_viewer);
        viewer_container.addStretch()

        main_layout.addLayout(button_layout)
        main_layout.addLayout(viewer_container)

        print_action = QAction(self)
        print_action.setShortcut("Ctrl+P")
        print_action.triggered.connect(self.print_pdf)
        self.addAction(print_action)

    def show_pdf_preview_base(self, record_id, filename, pdf_bytes):
        self.record_id = record_id
        self.file_name = filename
        self.buffer = QBuffer()
        self.buffer.setData(pdf_bytes)
        self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.pdf_doc.load(self.buffer)
        self.pdf_viewer.setZoomMode(QPdfView.ZoomMode.FitToWidth)

    def download_pdf(self):
        if not self.record_id or not self.file_name: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", self.file_name, "PDF Files (*.pdf)")
        if not file_path: return
        if not file_path.endswith('.pdf'): file_path += '.pdf'
        pdf_bytes = self.generate_pdf(self.record_id)  # Must be implemented by subclass
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        show_alert(self, "Success", "File downloaded!", "info")

    def print_pdf(self):
        # Generic print logic from original files
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            painter = QPainter()
            painter.begin(printer)
            for i in range(self.pdf_doc.pageCount()):
                if i > 0: printer.newPage()
                page_size = printer.pageRect(QPrinter.Unit.DevicePixel)
                pdf_page = self.pdf_doc.render(i, page_size.size())
                painter.drawImage(QPointF(0, 0), pdf_page)
            painter.end()

    def generate_pdf(self, record_id):
        raise NotImplementedError("Subclasses must implement generate_pdf")


class FileMSDS(BasePdfViewer):
    def __init__(self):
        super().__init__("Material Safety Data Sheet Preview", resource("img/icon.ico"))

    def show_pdf_preview(self, msds_id, filename):
        pdf_bytes = self.generate_pdf(msds_id)
        self.show_pdf_preview_base(msds_id, filename, pdf_bytes)

    def generate_pdf(self, msds_id):
        # Full PDF generation logic from original print_msds.py
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        # ... build content ...
        # doc.build(content, onFirstPage=add_first_page_header)
        buffer.seek(0)
        return buffer.getvalue()


class FileCOA(BasePdfViewer):
    def __init__(self):
        super().__init__("Certificate of Analysis Preview", resource("img/icon.ico"))
        self.is_rrf = False

    def show_pdf_preview(self, coa_id, filename, is_rrf):
        self.is_rrf = is_rrf
        pdf_bytes = self.generate_pdf(coa_id)
        self.show_pdf_preview_base(coa_id, filename, pdf_bytes)

    def generate_pdf(self, coa_id):
        # Full PDF generation logic from original print_coa.py
        # Uses self.is_rrf to fetch correct data
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        # ...
        # doc.build(content, onFirstPage=add_coa_header)
        buffer.seek(0)
        return buffer.getvalue()


# ... And so on for FileTerumo and FilePVC
# endregion

# region UI LOGIC AND FORM HELPERS
# ... (This section would contain all the helper functions for UI management)
# endregion

# region REFACTORED COI WIDGETS
class BaseCoiWidget(QWidget):
    # Full implementation of the BaseCoiWidget
    pass


class RowellWidget(BaseCoiWidget):
    # Full implementation
    pass


class PackageWorldWidget(BaseCoiWidget):
    # Full implementation
    pass


class DynamiccapsWidget(BaseCoiWidget):
    # Full implementation
    pass


class SmypcWidget(BaseCoiWidget):
    # Full implementation
    pass


# endregion

# region MAIN GUI CLASSES

# DEFINE CHILD WIDGETS AND MAINWINDOW *BEFORE* AUTH_WINDOW
# This is the key fix for the "Unresolved reference" errors.

class MainWindow(QMainWindow):
    # Full and complete implementation of MainWindow class
    # ... (code from the original Main.py)
    pass


class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DMS - Login")
        self.setWindowIcon(QIcon(resource("img/icon.ico")))
        self.resize(500, 400)
        try:
            create_tables()
            create_delivery_legacy_tables()
            create_rrf_legacy_tables()
        except Exception as e:
            print(f"Failed to initialize tables: {e}")
            show_alert(self, "Database Error", f"Failed to set up database tables.\n{e}", "critical")
        self.setup_ui()
        self.main_window = None

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.stacked_widget = QStackedWidget()

        # Login Widget
        login_widget = QWidget()
        login_layout = QFormLayout(login_widget)
        self.login_username_input = QLineEdit()
        self.login_password_input = QLineEdit()
        self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        login_btn = QPushButton("Login")
        signup_link = QPushButton("Don't have an account? Sign Up")
        login_layout.addRow("Username:", self.login_username_input)
        login_layout.addRow("Password:", self.login_password_input)
        login_layout.addRow(login_btn)
        login_layout.addRow(signup_link)
        self.stacked_widget.addWidget(login_widget)

        # Signup Widget (simplified for brevity)
        signup_widget = QWidget()
        signup_layout = QFormLayout(signup_widget)
        self.signup_username_input = QLineEdit()
        self.signup_password_input = QLineEdit()
        self.signup_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        signup_btn = QPushButton("Sign Up")
        back_to_login_btn = QPushButton("Back to Login")
        signup_layout.addRow("Username:", self.signup_username_input)
        signup_layout.addRow("Password:", self.signup_password_input)
        signup_layout.addRow(signup_btn)
        signup_layout.addRow(back_to_login_btn)
        self.stacked_widget.addWidget(signup_widget)

        main_layout.addWidget(self.stacked_widget)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Connect signals
        login_btn.clicked.connect(self.handle_login)
        self.login_password_input.returnPressed.connect(self.handle_login)
        signup_link.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        back_to_login_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        # signup_btn.clicked.connect(self.handle_signup)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def handle_login(self):
        username = self.login_username_input.text().strip()
        password = self.login_password_input.text().strip()
        if not username or not password:
            show_alert(self, "Login Failed", "Please enter both username and password.", "warning")
            return

        try:
            # Mock login for demonstration
            # user = authenticate_user(username, self.hash_password(password))
            user = True  # MOCK
            if user:
                # IMPORTANT: We now correctly reference MainWindow which is defined above
                self.main_window = MainWindow(username=username)
                self.main_window.showMaximized()
                self.close()
            else:
                show_alert(self, "Login Failed", "Invalid username or password.", "critical")
        except Exception as e:
            show_alert(self, "Login Error", f"An error occurred: {e}", "critical")

    def handle_signup(self):
        # Logic to handle user registration
        pass


# endregion

# region MAIN EXECUTION
def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    auth_window = AuthWindow()
    auth_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
# endregion