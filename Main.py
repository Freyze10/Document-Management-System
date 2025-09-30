from PyQt6.QtCore import Qt, QDate, QRegularExpression, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QRegularExpressionValidator, QFont, QAction
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTabWidget, \
    QTableWidget, QLineEdit, QHeaderView, QTableWidgetItem, QScrollArea, QTextEdit, QPushButton, QDateEdit, \
    QMessageBox, QAbstractItemView, QGroupBox, QCompleter, QDialog, QLabel, QProgressBar, QStackedLayout
from db import db_con, db_dr, db_rrf
from alert import window_alert
from table import msds_data_entry, coa_data_entry, table, terumo, korpack
from print.print_msds import FileMSDS
from print.print_coa import FileCOA
from print.print_terumo import FileTerumo
import Login
from utils import abs_path, scroll_date, calendar_design


class MainWindow(QMainWindow):
    def __init__(self, username=None):
        super().__init__()

        self.main_layout = QVBoxLayout()
        self.main_tabs = QTabWidget()

        self.username = username  # Store the username

        self.msds_form_layout = QVBoxLayout()
        self.msds_btn_layout = QHBoxLayout()
        self.coa_btn_layout = QHBoxLayout()
        self.terumo_btn_layout = QHBoxLayout()  # New for Terumo format
        self.korpack_btn_layout = QHBoxLayout()
        self.coa_form_layout = QVBoxLayout()
        self.terumo_form_layout = QVBoxLayout()
        self.korpack_form_layout = QVBoxLayout()

        # MSDS FORM init
        #Section 1
        self.customer_name_input = QLineEdit()
        self.trade_label_input = QLineEdit()
        self.manufactured_label_input = QTextEdit()
        self.manufactured_label_input.setTabChangesFocus(True)
        self.tel_label_input = QLineEdit()
        tel_regex = QRegularExpression(r'^(\d{7,12}|\(\d{1,4}\)\s?\d{6,10})$')
        tel_validator = QRegularExpressionValidator(tel_regex)
        self.tel_label_input.setValidator(tel_validator)
        self.tel_label_timer = self.setup_finished_typing(
            self.tel_label_input, self.check_tel_number, delay=3000
        )

        self.facsimile_label_input = QLineEdit()
        self.facsimile_label_input.setValidator(tel_validator)
        self.facsimile_label_timer = self.setup_finished_typing(
            self.facsimile_label_input, self.check_tel_number, delay=3000
        )
        self.email_label_input = QLineEdit()
        email_regex = QRegularExpression(r'^[\w\.-]+@[\w\.-]+\.\w{2,4}$')
        email_validator = QRegularExpressionValidator(email_regex)
        self.email_label_input.setValidator(email_validator)
        self.email_label_timer = self.setup_finished_typing(
            self.email_label_input, self.check_email, delay=3000
        )

        #Section2
        self.composition_input = QTextEdit()
        self.composition_input.setTabChangesFocus(True)
        #Section3
        self.hazard_preliminaries_input = QLineEdit()
        self.hazard_entry_route_input = QLineEdit()
        self.hazard_symptoms_input = QLineEdit()
        self.hazard_restrictive_condition_input = QLineEdit()
        self.hazard_eyes_input = QLineEdit()
        self.hazard_general_note_input = QLineEdit()
        self.hazard_single_field_input = QLineEdit()
        #Section4
        self.first_aid_inhalation_input = QLineEdit()
        self.first_aid_eyes = QLineEdit()
        self.first_aid_skin_input = QLineEdit()
        self.first_aid_ingestion_input = QLineEdit()
        #Section5
        self.fire_fighting_media_input = QTextEdit()
        self.fire_fighting_media_input.setTabChangesFocus(True)
        #Section6
        self.accidental_release_input = QTextEdit()
        self.accidental_release_input.setTabChangesFocus(True)
        #Section7
        self.handling_input = QLineEdit()
        self.msds_storage_input = QLineEdit()
        self.msds_storage_single_input = QLineEdit()
        #Section8
        self.exposure_control_input = QLineEdit()
        self.respiratory_protection_input = QLineEdit()
        self.hand_protection_input = QLineEdit()
        self.eye_protection_input = QLineEdit()
        self.skin_protection_input = QLineEdit()
        #Section9
        self.physical_property_rows = []
        #Section10
        self.stability_reactivity_input = QTextEdit()
        self.stability_reactivity_input.setTabChangesFocus(True)
        self.conditions_to_avoid_input = QLineEdit("None")
        self.materials_to_avoid_input = QLineEdit("None")
        self.hazardous_decomposition_input = QLineEdit("None")
        #Section11
        self.toxicological_input = QTextEdit()
        self.toxicological_input.setTabChangesFocus(True)
        #Section12
        self.ecological_input = QTextEdit()
        self.ecological_input.setTabChangesFocus(True)
        #Section13
        self.disposal_input = QTextEdit()
        self.disposal_input.setTabChangesFocus(True)
        #Section14
        self.transport_input = QTextEdit()
        self.transport_input.setTabChangesFocus(True)
        #Section15
        self.regulatory_input = QTextEdit()
        self.regulatory_input.setTabChangesFocus(True)
        #Section16
        self.msds_shelf_life_input = QTextEdit()
        self.msds_shelf_life_input.setTabChangesFocus(True)
        #Section17
        self.other_input = QTextEdit()
        self.other_input.setTabChangesFocus(True)
        #Submit Button
        self.btn_msds_submit = QPushButton("Submit")
        self.btn_msds_submit.setProperty("class", "msds_submit_btn")
        self.btn_msds_submit.clicked.connect(self.msds_btn_submit_clicked)

        # msds form switch
        self.hazard_stacked_layout = QStackedLayout()
        self.handling_storage_stacked_layout = QStackedLayout()

        self.hazard_group = QGroupBox("3) Hazard Information")
        self.hazard_group_v_layout = QVBoxLayout(self.hazard_group)

        self.handling_storage_group = QGroupBox("7) Handling and Storage")
        self.handling_storage_group_v_layout = QVBoxLayout(self.handling_storage_group)

        # COA form init
        #summary of analysis table
        self.summary_analysis_table = QTableWidget()
        #inputs variable
        self.coa_customer_input = QLineEdit()
        self.color_code_input = QLineEdit()
        self.color_code_timer = self.setup_finished_typing(
            self.color_code_input,
            lambda: coa_data_entry.populate_coa_summary(self),
            delay=1200
        )
        self.quantity_delivered_input = QLineEdit()
        self.delivery_date_input = QDateEdit()
        self.delivery_date_input.setCalendarPopup(True)
        self.delivery_date_input.setDate(QDate.currentDate())
        self.delivery_date_input.calendarWidget().setMinimumSize(370, 230)
        self.delivery_date_input.calendarWidget().setStyleSheet(calendar_design.STYLESHEET)
        # Disable scroll for delivery_date_input
        self.wheel_filter = scroll_date.DateWheelEventFilter()
        self.delivery_date_input.installEventFilter(self.wheel_filter)

        self.lot_number_input = QLineEdit()
        self.production_date_input = QDateEdit()
        self.production_date_input.setCalendarPopup(True)
        self.production_date_input.setDate(QDate(QDate.currentDate().year(), QDate.currentDate().month(), 1))
        self.production_date_input.calendarWidget().setMinimumSize(370, 230)
        self.production_date_input.calendarWidget().setStyleSheet(calendar_design.STYLESHEET)
        self.production_date_input.installEventFilter(self.wheel_filter)

        self.is_rrf = False
        self.delivery_receipt_label = QLabel("Delivery Receipt No:")
        self.coa_header_label = QLabel("Certificate of Analysis")
        self.dr_no_list = db_con.get_all_dr_no()
        self.rrf_no_list = db_con.get_all_rrf_no()
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
        self.dr_completer = QCompleter(self.dr_no_list)
        self.dr_completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)  # Suggest if text is contained anywhere
        self.delivery_receipt_input = QLineEdit()
        self.dr_completer.popup().setStyleSheet(style_completer)
        self.delivery_receipt_input.setCompleter(self.dr_completer)
        self.delivery_receipt_timer = self.setup_finished_typing(
            self.delivery_receipt_input,
            lambda: coa_data_entry.populate_coa_fields(self, self.delivery_receipt_input.text()),
            delay=1200
        )
        self.sync_button = QPushButton("Sync")
        self.sync_button.setFixedSize(60, 25)
        self.sync_button.clicked.connect(self.run_sync_script)
        self.terumo_sync_button = QPushButton("Sync")
        self.terumo_sync_button.setFixedSize(60, 25)
        self.terumo_sync_button.clicked.connect(self.run_sync_script)
        self.po_number_input = QLineEdit()
        self.certified_completer = QCompleter(self.certified_by_lists)
        self.certified_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.certified_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.certified_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.certified_completer.setCurrentRow(0)
        self.certified_by_input = QLineEdit()
        self.certified_completer.popup().setStyleSheet(style_completer)
        self.certified_by_input.setCompleter(self.certified_completer)
        self.creation_date_input = QDateEdit()
        self.creation_date_input.setCalendarPopup(True)
        self.creation_date_input.setDate(QDate.currentDate())
        self.creation_date_input.calendarWidget().setMinimumSize(370, 230)
        self.creation_date_input.calendarWidget().setStyleSheet(calendar_design.STYLESHEET)
        self.creation_date_input.installEventFilter(self.wheel_filter)
        self.coa_storage_input = QLineEdit()
        self.coa_shelf_life_input = QLineEdit()
        self.suitability_input = QLineEdit()
        self.btn_coa_submit = QPushButton("Submit")
        self.btn_coa_submit.clicked.connect(self.coa_btn_submit_clicked)

        # TERUMO COA inputs
        self.terumo_delivery_receipt = QLineEdit()
        self.terumo_delivery_receipt.setCompleter(self.dr_completer)
        self.terumo_delivery_receipt_timer = self.setup_finished_typing(
            self.terumo_delivery_receipt,
            lambda: terumo.populate_terumo_coa_fields(self, self.terumo_delivery_receipt.text()),
            delay=1200
        )
        self.terumo_customer_input = QLineEdit()
        self.terumo_item_code = QLineEdit()
        self.terumo_item_description = QLineEdit()
        self.terumo_item_decription_timer = self.setup_finished_typing(
            self.terumo_item_description,
            lambda: terumo.populate_item_code(self, self.terumo_item_description.text()),
            delay=1200
        )
        self.terumo_lot_number = QLineEdit()
        self.terumo_lot_timer = self.setup_finished_typing(
            self.terumo_lot_number,
            lambda: terumo.seperate_lots(self, self.terumo_lot_number.text()),
            delay=1200
        )
        self.terumo_quantity = QLineEdit()
        self.terumo_delivery_date = QDateEdit()
        self.terumo_delivery_date.setCalendarPopup(True)
        self.terumo_delivery_date.setDate(QDate.currentDate())
        self.terumo_delivery_date.calendarWidget().setMinimumSize(370, 230)
        self.terumo_delivery_date.calendarWidget().setStyleSheet(calendar_design.STYLESHEET)
        self.terumo_delivery_date.installEventFilter(self.wheel_filter)
        self.terumo_color_std = QLineEdit("TPC approved standard")
        self.terumo_color_actual = QLineEdit("Same as standard")
        self.terumo_color_judgement = QLineEdit("Passed")
        self.terumo_foreign_diameter1 = QLineEdit("> 0.10 - 0.35")
        self.terumo_foreign_diameter2 = QLineEdit("> 0.01 - 0.10")
        self.terumo_foreign_area1 = QLineEdit("< 0.10")
        self.terumo_foreign_area2 = QLineEdit("< 0.10")
        self.terumo_foreign_count1 = QLineEdit("2 pcs")
        self.terumo_foreign_count2 = QLineEdit("6 pcs")
        self.terumo_foreign_actual1 = QLineEdit("0")
        self.terumo_foreign_actual2 = QLineEdit("0")
        self.terumo_foreign_judgement = QLineEdit("Passed")
        self.terumo_appearance_std = QLineEdit("Free from foreign material. No stickiness of pellets")
        self.terumo_appearance_start = QLineEdit("0")
        self.terumo_appearance_mid = QLineEdit("0")
        self.terumo_appearance_end = QLineEdit("0")
        self.terumo_appearance_judgement = QLineEdit("Passed")
        self.terumo_dimension_std = QTextEdit()
        self.terumo_dimension_std.setPlainText(
            "3 x 3 ± 0.5 mm pellet diameter and length\n\n"
            "Single cut, partially cut or double pellet shall be treated as single pellet and must be within the set acceptance criteria"
        )
        self.terumo_dimension_start = QLineEdit("2.5x3.5")
        self.terumo_dimension_middle = QLineEdit("2.6x3.5")
        self.terumo_dimension_end = QLineEdit("2.5x3.5")
        self.terumo_dimension_judgement = QLineEdit("Passed")
        self.terumo_lots = QTextEdit()
        self.terumo_approved_by = QLineEdit()
        self.terumo_approved_by.setCompleter(self.certified_completer)
        self.terumo_approved_by.returnPressed.connect(self.terumo_submit_clicked)
        self.terumo_approver_position = QLineEdit()
        self.terumo_approver_position.returnPressed.connect(self.terumo_submit_clicked)
        self.terumo_submit_btn = QPushButton("Submit")
        self.terumo_submit_btn.clicked.connect(self.terumo_submit_clicked)
        self.all_terumo_id = db_con.get_all_terumo_id()

        # korpack COA Inputs
        self.korpack_dr_no = QLineEdit()
        self.korpack_dr_no.setCompleter(self.dr_completer)
        self.korpack_delivery_receipt_timer = self.setup_finished_typing(
            self.korpack_dr_no,
            lambda: korpack.populate_korpack_coa_fields(self, self.korpack_dr_no.text()),
            delay=1200
        )
        self.korpack_customer = QLineEdit()
        self.korpack_product_name = QLineEdit()
        self.korpack_lot_number = QLineEdit()
        self.korpack_quantity_delivered = QLineEdit()
        self.korpack_manufacturing_date = QDateEdit()
        self.korpack_manufacturing_date.setCalendarPopup(True)
        self.korpack_manufacturing_date.setDate(QDate.currentDate())
        self.korpack_manufacturing_date.calendarWidget().setStyleSheet(calendar_design.STYLESHEET)
        self.korpack_manufacturing_date.installEventFilter(self.wheel_filter)
        self.korpack_delivery_date = QDateEdit()
        self.korpack_delivery_date.setCalendarPopup(True)
        self.korpack_delivery_date.setDate(QDate.currentDate())
        self.korpack_delivery_date.calendarWidget().setStyleSheet(calendar_design.STYLESHEET)
        self.korpack_delivery_date.installEventFilter(self.wheel_filter)
        self.korpack_physical_form = QLineEdit()
        self.korpack_heat_suitability = QLineEdit()
        self.korpack_light_fastness = QLineEdit()
        self.korpack_migration = QLineEdit()
        self.korpack_swatch_dosage = QLineEdit()
        self.korpack_product_application = QLineEdit()
        self.korpack_packaging_form = QLineEdit()
        self.korpack_regulatory_info = QTextEdit()
        self.korpack_approved_by = QLineEdit()
        self.korpack_approver_position = QLineEdit()
        self.korpack_btn_submit = QPushButton("Submit")
        self.korpack_btn_submit.clicked.connect(self.korpack_btn_submit_clicked)

        self.coa_widget = None
        self.msds_widget = None
        self.terumo_widget = None
        self.korpack_widget = None

        self.msds_tab = QWidget()  #MSDS Main Tab
        self.msds_layout = QVBoxLayout(self.msds_tab)

        self.msds_sub_tabs = QTabWidget()
        self.msds_layout.addWidget(self.msds_sub_tabs)

        self.msds_data_entry_tab = QWidget()
        self.msds_records_tab = QWidget()

        self.coa_tab = QWidget()  # COA Main Tab
        self.coa_layout = QVBoxLayout(self.coa_tab)

        self.coa_sub_tabs = QTabWidget()
        self.coa_layout.addWidget(self.coa_sub_tabs)

        self.coa_data_entry_tab = QWidget()
        self.coa_records_tab = QWidget()

        # SUB-TAB
        self.msds_sub_tabs.addTab(self.msds_records_tab, "Records")
        self.msds_sub_tabs.addTab(self.msds_data_entry_tab, "Data Entry")

        self.coa_sub_tabs.addTab(self.coa_records_tab, "Records")
        self.coa_sub_tabs.addTab(self.coa_data_entry_tab, "Data Entry")

        # COA Data Entry sub-tabs
        self.coa_data_entry_sub_tabs = QTabWidget()
        self.coa_default_tab = QWidget()
        self.coa_terumo_tab = QWidget()
        self.coa_korpack_tab = QWidget()
        self.coa_data_entry_sub_tabs.addTab(self.coa_default_tab, "COA")
        self.coa_data_entry_sub_tabs.addTab(self.coa_terumo_tab, "Terumo (COA)")
        self.coa_data_entry_sub_tabs.addTab(self.coa_korpack_tab, "korpack (COA)")
        self.coa_data_entry_layout = QVBoxLayout(self.coa_data_entry_tab)
        self.coa_data_entry_layout.addWidget(self.coa_data_entry_sub_tabs)

        # Default COA scroll and layout
        self.coa_scroll_area = QScrollArea(self.coa_default_tab)
        self.coa_scroll_area.setWidgetResizable(True)
        coa_form_container = QWidget()
        coa_form_layout = QVBoxLayout(coa_form_container)
        coa_form_layout.addLayout(self.coa_form_layout)
        coa_form_layout.addLayout(self.coa_btn_layout)
        self.coa_scroll_area.setWidget(coa_form_container)
        coa_tab_layout = QVBoxLayout(self.coa_default_tab)
        coa_tab_layout.addWidget(self.coa_scroll_area)

        # Terumo COA scroll and layout
        self.terumo_scroll_area = QScrollArea(self.coa_terumo_tab)
        self.terumo_scroll_area.setWidgetResizable(True)
        terumo_form_container = QWidget()
        terumo_form_layout = QVBoxLayout(terumo_form_container)
        terumo_form_layout.addLayout(self.terumo_form_layout)
        terumo_form_layout.addLayout(self.terumo_btn_layout)
        self.terumo_scroll_area.setWidget(terumo_form_container)
        terumo_tab_layout = QVBoxLayout(self.coa_terumo_tab)
        terumo_tab_layout.addWidget(self.terumo_scroll_area)

        # korpack COA scroll and layout
        self.korpack_scroll_area = QScrollArea(self.coa_korpack_tab)
        self.korpack_scroll_area.setWidgetResizable(True)
        korpack_form_container = QWidget()
        korpack_form_layout = QVBoxLayout(korpack_form_container)
        korpack_form_layout.addLayout(self.korpack_form_layout)
        korpack_form_layout.addLayout(self.korpack_btn_layout)
        self.korpack_scroll_area.setWidget(korpack_form_container)
        korpack_tab_layout = QVBoxLayout(self.coa_korpack_tab)
        korpack_tab_layout.addWidget(self.korpack_scroll_area)

        self.main_tabs.addTab(self.msds_tab, "MSDS")
        self.main_tabs.addTab(self.coa_tab, "CoA")
        self.msds_tab.setObjectName("msds_tab")
        self.coa_tab.setObjectName("coa_tab")

        self.user_widget = UserWidget(self.username)
        self.main_tabs.setCornerWidget(self.user_widget, Qt.Corner.TopRightCorner)
        self.user_widget.logout_requested.connect(self.logout)

        self.msds_search_bar = QLineEdit()
        self.msds_search_bar.setPlaceholderText("Search...")
        search_icon_msds = QAction(QIcon(abs_path.resource("img/search_icon.png")), "Search", self.msds_search_bar)
        self.msds_search_bar.addAction(search_icon_msds, QLineEdit.ActionPosition.TrailingPosition)
        self.coa_search_bar = QLineEdit()
        self.coa_search_bar.setPlaceholderText("Search...")
        search_icon_coa = QAction(QIcon(abs_path.resource("img/search_icon.png")), "Search", self.coa_search_bar)
        self.coa_search_bar.addAction(search_icon_coa, QLineEdit.ActionPosition.TrailingPosition)

        self.coa_corner = QWidget()
        self.coa_corner_h = QHBoxLayout(self.coa_corner)
        self.coa_corner_h.setContentsMargins(0, 0, 0, 0)
        self.coa_corner_h.setSpacing(12)
        self.btn_switch_rrf = QPushButton()
        self.btn_switch_rrf.setCheckable(True)
        self.btn_switch_rrf.setText("Switch to RRF")
        self.btn_switch_rrf.toggled.connect(self.toggle_rrf)

        self.coa_corner_h.addWidget(self.btn_switch_rrf)
        self.coa_corner_h.addWidget(self.coa_search_bar)

        self.btn_switch_rrf.setFixedHeight(32)
        self.btn_switch_rrf.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)

        self.msds_sub_tabs.setCornerWidget(self.msds_search_bar)
        self.coa_sub_tabs.setCornerWidget(self.coa_corner)

        self.msds_sub_tabs.currentChanged.connect(self.toggle_msds_search_bar)
        self.coa_sub_tabs.currentChanged.connect(self.toggle_coa_search_bar)
        self.msds_search_bar.setFocus()
        self.coa_search_bar.setFocus()
        self.msds_records_table = QTableWidget()
        self.msds_records_table.setProperty("class", "records_table")

        self.msds_records_layout = QVBoxLayout(self.msds_records_tab)  # inside MSDS sub-tab Records
        self.msds_records_layout.addWidget(self.msds_records_table)

        self.msds_scroll_area = QScrollArea(self.msds_data_entry_tab)
        self.msds_scroll_area.setWidgetResizable(True)

        # Form container inside the scroll area
        msds_form_container = QWidget()
        msds_form_layout = QVBoxLayout(msds_form_container)

        msds_form_layout.addLayout(self.msds_form_layout)
        msds_form_layout.addLayout(self.msds_btn_layout)

        self.msds_scroll_area.setWidget(msds_form_container)

        # Final layout for the tab
        self.msds_data_entry_layout = QVBoxLayout(self.msds_data_entry_tab)
        self.msds_data_entry_layout.addWidget(self.msds_scroll_area)

        #Inside COA Records Tab
        self.coa_records_table = QTableWidget()
        self.coa_records_table.setProperty("class", "records_table")

        self.coa_records_layout = QVBoxLayout(self.coa_records_tab)  # inside COA sub-tab Records
        self.coa_records_layout.addWidget(self.coa_records_table)

        self.main_layout.addWidget(self.main_tabs)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)
        search_style = """
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 15px;
                padding: 4px 20px 6px 10px;
                background-color: #f9f9f9;
                font-size: 12px;
                margin-bottom: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #4a90e2;
                background-color: #ffffff;
            }
        """
        self.setStyleSheet("""
            QTableWidget[class="records_table"] {
                font-size: 15px;  /* Larger cell font */
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 8px;  /* Rounded corners */
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);  /* Subtle shadow */
            }
            QTableWidget[class="records_table"]::item {
                padding: 12px;  /* Increased padding */
                border-bottom: 1px solid #e0e0e0;
                background-color: #ffffff;
            }
            QTableWidget[class="records_table"]::item:alternate {
                background-color: #f9fafb;  /* Alternating row color */
            }
            QTableWidget[class="records_table"]::item:selected {
                background-color: #e3f2fd;  /* Match coa_data_entry selection */
                color: #000000;
                border: 2px solid #0078d7;
            }
            QTableWidget[class="records_table"]::item:hover {
                background-color: #e9f3ff;  /* Match coa_data_entry hover */
            }
            QTableWidget[class="records_table"] QHeaderView::section {
                font-size: 16px;  /* Larger header font */
                font-weight: 600;
                padding: 12px;
                background-color: #f0f4f8;  /* Slightly lighter header */
                border: 1px solid #d1d5db;
                color: #1a3c6c;
            }
            QTableWidget[class="records_table"] QHeaderView::section:horizontal {
                border-right: none;
                border-bottom: 3px solid #4a90e2;  /* Blue underline */
            }
            QTableCornerButton::section {
                background-color: #f0f4f8;
                border: 1px solid #d1d5db;
            }
            QPushButton[class="msds_submit_btn"] {
                background-color: #4CAF50;
                color: white;
                padding: 12px 26px;
                margin: 0 70px 20px 0;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton[class="msds_submit_btn"]:hover {
                background-color: #45a049;
            }
            QPushButton[class="msds_submit_btn"]:pressed {
                background-color: #3e8e41;
            }
            QWidget#msds_tab, QWidget#coa_tab, QTabWidget {
                background-color: #f2f2f2;
                border: none;
            }
        """)
        tab_menu_style = """
            QTabWidget::pane {
                border: 1px solid #0066cc;
                border-radius: 6px;
                background-color: #f0f0f0;
                top: -1px;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #333;
                padding: 8px 12px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-bottom: 1px solid #0066cc;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                margin-top: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0078d7;
                font-weight: bold;
                border: 1px solid #0078d7;
                border-bottom: none;
                margin-top: 0px;
            }
            QTabBar::tab:hover {
                background: #e9f3ff;
                color: #005a9e;
            }
        """
        main_tab_style = """
            QTabBar::tab {
                background: #fafafa;
                color: #444;
                padding: 7px 16px;
                font-size: 14px;
                border: 1px solid #bbb;
                border-radius: 4px 4px 0 0;
                margin-right: 3px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0066cc;
                font-weight: bold;
                border: 1px solid #0066cc;
            }
            QTabBar::tab:hover {
                background: #f0f7ff;
                color: #004a99;
            }
        """

        self.main_tabs.tabBar().setStyleSheet(main_tab_style)
        self.msds_sub_tabs.setStyleSheet(tab_menu_style)
        self.coa_sub_tabs.setStyleSheet(tab_menu_style)
        self.msds_search_bar.setStyleSheet(search_style)
        self.coa_search_bar.setStyleSheet(search_style)

        self.last_hovered = None
        self.msds_table_records_init()
        self.coa_table_records_init()
        # connect hover and clicked functions on table
        self.msds_records_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.msds_records_table.setMouseTracking(True)
        self.msds_records_table.cellEntered.connect(self.on_cell_hover)
        self.msds_records_table.cellClicked.connect(self.msds_cell_clicked)
        # connect search function
        self.msds_label_timer = self.setup_finished_typing(
            self.msds_search_bar,
            lambda: table.search_msds(self, self.msds_search_bar.text()),
            delay=600
        )
        self.coa_records_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.coa_records_table.setMouseTracking(True)
        self.coa_records_table.cellEntered.connect(self.on_cell_hover)
        self.coa_records_table.cellClicked.connect(self.coa_cell_clicked)
        self.coa_label_timer = self.setup_finished_typing(
            self.coa_search_bar,
            lambda: table.search_coa(self, self.coa_search_bar.text()),
            delay=600
        )
        table.load_msds_table(self)
        table.load_coa_table(self)
        coa_data_entry.coa_data_entry_form(self)
        msds_data_entry.create_form(self)
        terumo.coa_entry_form(self)
        korpack.clear_korpack_form(self)
        korpack.create_korpack_form(self)

    def msds_btn_submit_clicked(self):
        try:
            general = self.hazard_general_note_input.text().strip() or self.hazard_single_field_input.text().strip()
            storage = self.msds_storage_input.text().strip() or self.msds_storage_single_input.text().strip()

            # Collect all required fields
            required_fields = {
                "Customer Name": self.customer_name_input.text(),
                "Trade Name": self.trade_label_input.text(),
                "Manufactured By": self.manufactured_label_input.toPlainText(),
                "Telephone No.": self.tel_label_input.text(),
                "Facsimile": self.facsimile_label_input.text(),
                "Email Address": self.email_label_input.text(),
                "Composition/Information on Ingredients": self.composition_input.toPlainText(),
                "Hazard General Note": general,
                "First Aid Inhalation": self.first_aid_inhalation_input.text(),
                "First Aid Eyes": self.first_aid_eyes.text(),
                "First Aid Skin": self.first_aid_skin_input.text(),
                "First Aid Ingestion": self.first_aid_ingestion_input.text(),
                "Extinguishing Media": self.fire_fighting_media_input.toPlainText(),
                "Accidental Release": self.accidental_release_input.toPlainText(),

                "Storage": storage,
                "Exposure Control": self.exposure_control_input.text(),
                "Respiratory Protection": self.respiratory_protection_input.text(),
                "Hand Protection": self.hand_protection_input.text(),
                "Eye Protection": self.eye_protection_input.text(),
                "Skin Protection": self.skin_protection_input.text(),

                "Stability & Reactivity": self.stability_reactivity_input.toPlainText(),
                "Conditions to avoid": self.conditions_to_avoid_input.text(),
                "Materials to avoid": self.materials_to_avoid_input.text(),
                "Hazardous decomposition": self.hazardous_decomposition_input.text(),
                "Toxicological": self.toxicological_input.toPlainText(),
                "Ecological": self.ecological_input.toPlainText(),
                "Disposal": self.disposal_input.toPlainText(),
                "Transport Information": self.transport_input.toPlainText(),
                "Regulatory": self.regulatory_input.toPlainText(),
                "Shelf Life": self.msds_shelf_life_input.toPlainText(),
                "Other": self.other_input.toPlainText()
            }

            # Check for empty values
            for field, value in required_fields.items():
                if not value.strip():  # empty string
                    window_alert.show_message(self, "Missing Input", f"Please fill in:   {field}", icon_type="warning")
                    return  # stop submission
            # If all fields are filled, proceed to save

            trade_name_text = self.trade_label_input.text().strip()
            product_code = trade_name_text.split()[-1] if trade_name_text else ""

            msds_data = {
                "customer_name": self.customer_name_input.text(),
                "trade_name": trade_name_text,
                "product_code": product_code,
                "manufacturer_info": self.manufactured_label_input.toPlainText(),
                "contact_tel": self.tel_label_input.text(),
                "contact_facsimile": self.facsimile_label_input.text(),
                "contact_email": self.email_label_input.text(),

                "composition_info": self.composition_input.toPlainText(),

                "hazard_preliminaries": self.hazard_preliminaries_input.text(),
                "hazard_entry_route": self.hazard_entry_route_input.text(),
                "hazard_symptoms": self.hazard_symptoms_input.text(),
                "hazard_restrictive_conditions": self.hazard_restrictive_condition_input.text(),
                "hazard_eyes": self.hazard_eyes_input.text(),
                "hazard_general_note": general,

                "first_aid_inhalation": self.first_aid_inhalation_input.text(),
                "first_aid_eyes": self.first_aid_eyes.text(),
                "first_aid_skin": self.first_aid_skin_input.text(),
                "first_aid_ingestion": self.first_aid_ingestion_input.text(),

                "fire_fighting_media": self.fire_fighting_media_input.toPlainText(),
                "accidental_release_info": self.accidental_release_input.toPlainText(),
                "handling_info": self.handling_input.text(),
                "storage_info": storage,

                "exposure_control_info": self.exposure_control_input.text(),
                "respiratory_protection": self.respiratory_protection_input.text(),
                "hand_protection": self.hand_protection_input.text(),
                "eye_protection": self.eye_protection_input.text(),
                "skin_protection": self.skin_protection_input.text(),

                "stability_reactivity": self.stability_reactivity_input.toPlainText(),
                "conditions_to_avoid": self.conditions_to_avoid_input.text(),
                "materials_to_avoid": self.materials_to_avoid_input.text(),
                "hazardous_decomposition": self.hazardous_decomposition_input.text(),
                "toxicological_info": self.toxicological_input.toPlainText(),
                "ecological_info": self.ecological_input.toPlainText(),
                "disposal_info": self.disposal_input.toPlainText(),
                "transport_info": self.transport_input.toPlainText(),
                "regulatory_info": self.regulatory_input.toPlainText(),
                "shelf_life_info": self.msds_shelf_life_input.toPlainText(),
                "other_info": self.other_input.toPlainText()
            }

            section9_data = {}
            for name_edit, value_edit in self.physical_property_rows:
                property_name = name_edit.text().strip()
                property_value = value_edit.text().strip()
                if property_name:  # Only add if the property name is not empty
                    section9_data[property_name] = property_value

            # Save
            try:
                if msds_data_entry.current_msds_id is not None:  # Update existing MSDS
                    db_con.update_msds_sheet(msds_data_entry.current_msds_id, msds_data, section9_data)
                    window_alert.show_message(self, "Success", "MSDS updated successfully!", icon_type="info")
                    msds_data_entry.current_msds_id = None
                else:  # Save new MSDS
                    db_con.save_msds_sheet(msds_data, section9_data)
                    window_alert.show_message(self, "Success", "MSDS saved successfully!", icon_type="info")
            except Exception as e:
                window_alert.show_message(self, "Database Error", str(e), icon_type="critical")
            finally:
                msds_data_entry.clear_msds_form(self)
                table.load_msds_table(self)
                self.msds_scroll_area.verticalScrollBar().setValue(0)
                self.msds_sub_tabs.setCurrentIndex(0)
        except Exception as e:
            window_alert.show_message(self, "Unexpected Error", f"An error occurred: {str(e)}", icon_type="critical")

    def coa_btn_submit_clicked(self):
        customer_name = self.coa_customer_input.text()
        color_code = self.color_code_input.text()
        quantity_delivered = self.quantity_delivered_input.text()
        delivery_date = self.delivery_date_input.date().toString("yyyy-MM-dd")
        lot_number = self.lot_number_input.text()
        production_date = self.production_date_input.date().toString("yyyy-MM-dd")
        delivery_receipt = self.delivery_receipt_input.text()
        po_number = self.po_number_input.text()
        summary_of_analysis = self.get_coa_summary_analysis_table_data()
        certified_by = self.certified_by_input.text()
        creation_date = self.creation_date_input.date().toString("yyyy-MM-dd")
        storage = self.coa_storage_input.text()
        shelf_life = self.coa_shelf_life_input.text()
        suitability = self.suitability_input.text()

        required_fields = {
            "Customer Name": customer_name,
            "Color Code": color_code,
            "Quantity Delivered": quantity_delivered,
            "Lot Number": lot_number,
            "Delivery Receipt": delivery_receipt,
            "Certified By": certified_by,
            "Storage": storage,
            "Shelf Life": shelf_life
        }

        # Check if any required field is empty
        for field, value in required_fields.items():
            if not value:  # empty string
                window_alert.show_message(self, "Missing Input", f"Please fill in:  {field}", icon_type="warning")
                return  # stop processing

        # Check summary of analysis if no empty row
        if not any(any(cell for cell in row) for row in summary_of_analysis.values()):
            window_alert.show_message(self, "Missing Input", "Please fill in the Summary of Analysis table.",
                                      icon_type="warning")
            return

            # Validate certified_by against the list from the database
        if certified_by not in self.certified_by_lists:
            window_alert.show_message(self, "Invalid Input", f"Certified By: '{certified_by}' is not in the list.",
                                      icon_type="warning")
            return

        # Build coa_data for saving
        coa_data = {
            "customer_name": customer_name,
            "color_code": color_code,
            "lot_number": lot_number,
            "po_number": po_number,
            "delivery_receipt": delivery_receipt,
            "quantity_delivered": quantity_delivered,
            "delivery_date": delivery_date,
            "production_date": production_date,
            "creation_date": creation_date,
            "certified_by": certified_by,
            "storage": storage,
            "shelf_life": shelf_life,
            "suitability": suitability
        }

        # Save
        try:
            if coa_data_entry.current_coa_id is not None:  # Update existing COA
                if self.is_rrf:  # RRF
                    db_con.update_certificate_of_analysis_rrf(coa_data_entry.current_coa_id, coa_data,
                                                              summary_of_analysis)
                    window_alert.show_message(self, "Success", f"Certificate of Analysis - RRF updated successfully!",
                                              icon_type="info")
                    coa_data_entry.current_coa_id = None
                else:  # COA
                    db_con.update_certificate_of_analysis(coa_data_entry.current_coa_id, coa_data, summary_of_analysis)
                    window_alert.show_message(self, "Success", f"Certificate of Analysis updated successfully!",
                                              icon_type="info")
                    coa_data_entry.current_coa_id = None

            else:  # Save new COA
                if self.is_rrf:  # RRF
                    db_con.save_certificate_of_analysis_rrf(coa_data, summary_of_analysis)
                    window_alert.show_message(self, "Success", f"Certificate of Analysis - RRF saved successfully!",
                                              icon_type="info")
                else:  # COA
                    db_con.save_certificate_of_analysis(coa_data, summary_of_analysis)
                    window_alert.show_message(self, "Success", f"Certificate of Analysis saved successfully!",
                                              icon_type="info")
        except Exception as e:
            window_alert.show_message(self, "Database Error", str(e), icon_type="critical")
        finally:
            coa_data_entry.clear_coa_form(self)
            if self.is_rrf:
                table.load_rrf_table(self)
            else:
                table.load_coa_table(self)
            coa_data_entry.adjust_table_height(self)
            self.coa_scroll_area.verticalScrollBar().setValue(0)
            self.coa_sub_tabs.setCurrentIndex(0)

    def terumo_submit_clicked(self):
        try:
            # Collect data (adapt as needed for DB)
            terumo_dr = self.terumo_delivery_receipt.text()
            customer_name = self.terumo_customer_input.text()
            quantity = self.terumo_quantity.text()
            delivery_date = self.terumo_delivery_date.date().toString("yyyy-MM-dd")
            lot_number = self.terumo_lot_number.text()
            approved_by = self.terumo_approved_by.text()

            item_code = self.terumo_item_code.text()
            item_desc = self.terumo_item_description.text()
            color_std = self.terumo_color_std.text()
            color_actual = self.terumo_color_actual.text()
            color_judgement = self.terumo_color_judgement.text()
            foreign_diameter1 = self.terumo_foreign_diameter1.text()
            foreign_diameter2 = self.terumo_foreign_diameter2.text()
            foreign_area1 = self.terumo_foreign_area1.text()
            foreign_area2 = self.terumo_foreign_area2.text()
            foreign_count1 = self.terumo_foreign_count1.text()
            foreign_count2 = self.terumo_foreign_count2.text()
            foreign_actual1 = self.terumo_foreign_actual1.text()
            foreign_actual2 = self.terumo_foreign_actual2.text()
            foreign_judgement = self.terumo_foreign_judgement.text()
            appearance_std = self.terumo_appearance_std.text()
            appearance_start = self.terumo_appearance_start.text()
            appearance_mid = self.terumo_appearance_mid.text()
            appearance_end = self.terumo_appearance_end.text()
            appearance_judgement = self.terumo_appearance_judgement.text()
            dimension_std = self.terumo_dimension_std.toPlainText()
            dimension_start = self.terumo_dimension_start.text()
            dimension_middle = self.terumo_dimension_middle.text()
            dimension_end = self.terumo_dimension_end.text()
            dimension_judgement = self.terumo_dimension_judgement.text()
            position = self.terumo_approver_position.text()
            lots = self.terumo_lots.toPlainText()
            # Required fields check
            required_fields = {
                "Customer Name": customer_name,
                "Item Code": item_code,
                "Item Description": item_desc,
                "Lot Number": lot_number,
                "Quantity": quantity,
                "Approved By": approved_by,
            }
            for field, value in required_fields.items():
                if not value.strip():
                    window_alert.show_message(self, "Missing Input", f"Please fill in: {field}", icon_type="warning")
                    return

            if approved_by not in self.certified_by_lists:
                window_alert.show_message(self, "Invalid Input", f"Certified By: '{approved_by}' is not in the list.",
                                          icon_type="warning")
                return

            # Build coa_data and summary
            coa_data = {
                "customer_name": customer_name,
                "color_code": "",
                "lot_number": lot_number,
                "po_number": "",
                "delivery_receipt": terumo_dr,
                "quantity_delivered": quantity,
                "delivery_date": delivery_date,
                "production_date": QDate.currentDate().toString("yyyy-MM-dd"),
                "creation_date": QDate.currentDate().toString("yyyy-MM-dd"),
                "certified_by": approved_by,
                "storage": "",
                "shelf_life": "",
                "suitability": ""
            }

            terumo_data = {
                "item_code": item_code,
                "item_description": item_desc,
                "color_std": color_std,
                "color_actual": color_actual,
                "color_judgement": color_judgement,
                "diameter_std": foreign_diameter1 + ", " + foreign_diameter2,
                "area_std": foreign_area1 + ", " + foreign_area2,
                "count_std": foreign_count1 + ", " + foreign_count2,
                "fmc_actual": foreign_actual1 + ", " + foreign_actual2,
                "fmc_judgement": foreign_judgement,
                "appearance_std": appearance_std,
                "appearance_start": appearance_start,
                "appearance_mid": appearance_mid,
                "appearance_end": appearance_end,
                "appearance_judgement": appearance_judgement,
                "dimension_std": dimension_std,
                "dimension_start": dimension_start,
                "dimension_mid": dimension_middle,
                "dimension_end": dimension_end,
                "dimension_judgement": dimension_judgement,
                "approver_position": position,
                "lot_numbers": lots
            }

            # Save (use existing DB function or create new)
            try:
                if terumo.current_coa_id is not None:
                    db_con.update_terumo_coa(terumo.current_coa_id, coa_data, terumo_data)
                    window_alert.show_message(self, "Success", "Terumo COA updated successfully!", icon_type="info")
                    terumo.current_coa_id = None
                else:
                    db_con.save_terumo_coa(coa_data, terumo_data)
                    window_alert.show_message(self, "Success", "Terumo COA saved successfully!", icon_type="info")
            except Exception as e:
                window_alert.show_message(self, "Database Error", str(e), icon_type="critical")
            finally:
                terumo.clear_coa_form(self)
                table.load_coa_table(self)
                self.terumo_scroll_area.verticalScrollBar().setValue(0)
                self.coa_sub_tabs.setCurrentIndex(0)
                self.all_terumo_id = db_con.get_all_terumo_id()
        except Exception as e:
            print(e)

    def korpack_btn_submit_clicked(self):
        def korpack_btn_submit_clicked(self):
            """Handle submission of the Korpack COA form."""
            try:
                # Collect data from form fields
                customer_name = self.korpack_customer.text()
                product_name = self.korpack_product_name.text()
                lot_number = self.korpack_lot_number.text()
                quantity_delivered = self.korpack_quantity_delivered.text()
                manufacturing_date = self.korpack_manufacturing_date.date().toString("yyyy-MM-dd")
                delivery_date = self.korpack_delivery_date.date().toString("yyyy-MM-dd")
                physical_form = self.korpack_physical_form.text()
                heat_suitability = self.korpack_heat_suitability.text()
                light_fastness = self.korpack_light_fastness.text()
                migration = self.korpack_migration.text()
                swatch_dosage = self.korpack_swatch_dosage.text()
                product_application = self.korpack_product_application.text()
                packaging_form = self.korpack_packaging_form.text()
                regulatory_info = self.korpack_regulatory_info.toPlainText()
                approved_by = self.korpack_approved_by.text()
                approver_position = self.korpack_approver_position.text()

                # Define required fields
                required_fields = {
                    "Customer Name": customer_name,
                    "Product Name": product_name,
                    "Lot Number": lot_number,
                    "Quantity Delivered": quantity_delivered,
                    "Physical Form": physical_form,
                    "Heat Suitability": heat_suitability,
                    "Light Fastness": light_fastness,
                    "Migration": migration,
                    "Swatch Dosage": swatch_dosage,
                    "Product Application": product_application,
                    "Packaging Form": packaging_form,
                    "Regulatory Information": regulatory_info,
                    "Approved By": approved_by,
                    "Approver Position": approver_position,
                }

                # Check for empty required fields
                for field, value in required_fields.items():
                    if not value.strip():
                        window_alert.show_message(self, "Missing Input", f"Please fill in: {field}",
                                                  icon_type="warning")
                        return

                # Validate approved_by against certified_by_lists
                if approved_by not in self.certified_by_lists:
                    window_alert.show_message(self, "Invalid Input",
                                              f"Approved By: '{approved_by}' is not in the list.",
                                              icon_type="warning")
                    return

                # Build coa_data for saving
                coa_data = {
                    "customer_name": customer_name,
                    "product_name": product_name,
                    "lot_number": lot_number,
                    "quantity_delivered": quantity_delivered,
                    "manufacturing_date": manufacturing_date,
                    "delivery_date": delivery_date,
                    "physical_form": physical_form,
                    "heat_suitability": heat_suitability,
                    "light_fastness": light_fastness,
                    "migration": migration,
                    "swatch_dosage": swatch_dosage,
                    "product_application": product_application,
                    "packaging_form": packaging_form,
                    "regulatory_info": regulatory_info,
                    "approved_by": approved_by,
                    "approver_position": approver_position,
                    "creation_date": QDate.currentDate().toString("yyyy-MM-dd")
                }

                # Save or update data
                try:
                    if hasattr(self, 'korpack') and self.korpack.current_korpack_id is not None:  # Update existing COA
                        db_con.update_korpack_coa(self.korpack.current_korpack_id, coa_data)
                        window_alert.show_message(self, "Success", "Korpack COA updated successfully!",
                                                  icon_type="info")
                        self.korpack.current_korpack_id = None
                    else:  # Save new COA
                        db_con.save_korpack_coa(coa_data)
                        window_alert.show_message(self, "Success", "Korpack COA saved successfully!", icon_type="info")
                except Exception as e:
                    window_alert.show_message(self, "Database Error", str(e), icon_type="critical")
                finally:
                    clear_korpack_form(self)
                    self.table.load_korpack_table(self)
                    self.adjust_table_height(self)
                    self.korpack_scroll_area.verticalScrollBar().setValue(0)
                    self.coa_sub_tabs.setCurrentIndex(0)
            except Exception as e:
                window_alert.show_message(self, "Unexpected Error", f"An error occurred: {str(e)}",
                                          icon_type="critical")

    def get_coa_summary_analysis_table_data(self):
        data = {}
        row_count = self.summary_analysis_table.rowCount()
        col_count = self.summary_analysis_table.columnCount()

        for row in range(row_count):
            # Get row header (vertical header text)
            header_item = self.summary_analysis_table.verticalHeaderItem(row)
            row_header = header_item.text() if header_item else f"Row {row}"

            # Get values in that row
            row_values = []
            for col in range(col_count):
                cell_item = self.summary_analysis_table.item(row, col)
                value = cell_item.text() if cell_item else ""
                row_values.append(value)

            # Store row header with its values
            data[row_header] = row_values

        return data

    def add_row_to_coa_summary_table(self):
        row_count = self.summary_analysis_table.rowCount()

        # Use the styled input function
        header_text, ok = window_alert.show_text_input(self, "New Row", "Enter row header:")

        if ok and header_text.strip():
            self.summary_analysis_table.insertRow(row_count)

            # Update headers
            current_headers = [self.summary_analysis_table.verticalHeaderItem(i).text()
                               for i in range(row_count)]
            current_headers.append(header_text.strip())
            self.summary_analysis_table.setVerticalHeaderLabels(current_headers)

            # Adjust table height
            coa_data_entry.adjust_table_height(self)

    def delete_row_from_coa_summary_table(self):
        selected_indexes = self.summary_analysis_table.selectionModel().selectedRows()

        if not selected_indexes:
            # No row selected, show a warning
            print(selected_indexes)
            window_alert.show_message(self, "Warning", "Please select a row to delete.", icon_type="warning")
            return

        row_to_delete = selected_indexes[0].row()  # Single selection, take the first

        # Show confirmation message
        confirm = window_alert.show_message(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete row {row_to_delete + 1}?",
            icon_type="question",
            is_confirmation=True
        )

        if confirm:
            self.summary_analysis_table.removeRow(row_to_delete)
            coa_data_entry.adjust_table_height(self)

    def create_readonly_item(self, text=None, icon_path=None, selectable=True, column_idx=None):
        item = QTableWidgetItem()

        if text is not None:
            item.setText(text)

        if icon_path is not None:
            item.setIcon(QIcon(icon_path))

        # Make the item read-only
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        if not selectable:
            # Remove the selectable flag but keep enabled to accept clicks
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

        if column_idx == 0:
            font = QFont()
            font.setPointSize(11)
            item.setFont(font)
        return item

    def msds_table_records_init(self):
        self.msds_records_table.setColumnCount(4)
        self.msds_records_table.setHorizontalHeaderLabels(["Name", "", "", ""])
        self.msds_records_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.msds_records_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.msds_records_table.horizontalHeader().setMinimumSectionSize(40)  # Minimum width for icon columns
        # Override resize event
        self.msds_records_table.resizeEvent = lambda event: table.resize_columns(self, self.msds_records_table, event)
        self.msds_records_table.verticalHeader().setDefaultSectionSize(44)  # Increased row height
        self.msds_records_table.verticalHeader().setFixedWidth(40)
        self.msds_records_table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msds_records_table.horizontalHeader().setFixedHeight(44)  # Match row height
        self.msds_records_table.setShowGrid(False)

    def coa_table_records_init(self):
        self.coa_records_table.setColumnCount(4)
        self.coa_records_table.setHorizontalHeaderLabels(["Name", "", "", ""])
        self.coa_records_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.coa_records_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.coa_records_table.horizontalHeader().setMinimumSectionSize(40)  # Minimum width for icon columns
        # Override resize event
        self.coa_records_table.resizeEvent = lambda event: table.resize_columns(self, self.coa_records_table, event)
        self.coa_records_table.verticalHeader().setDefaultSectionSize(44)  # Increased row height
        self.coa_records_table.verticalHeader().setFixedWidth(40)
        self.coa_records_table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.coa_records_table.horizontalHeader().setFixedHeight(44)  # Match row height
        self.coa_records_table.setShowGrid(False)

    def on_cell_hover(self, row, column):
        table = self.sender()

        # Restore last hovered cell
        if hasattr(self, "last_hovered") and self.last_hovered:
            last_row, last_col = self.last_hovered
            last_item = table.item(last_row, last_col)  # get fresh reference
            if last_item:
                if last_col == 1:
                    last_item.setIcon(QIcon(abs_path.resource("img/view_icon.png")))  # normal view icon
                elif last_col == 2:
                    last_item.setIcon(QIcon(abs_path.resource("img/edit_icon.png")))  # normal edit icon
                elif last_col == 3:
                    last_item.setIcon(QIcon(abs_path.resource("img/delete_icon.png")))  # normal delete icon
            self.last_hovered = None

        # Apply highlight to the current cell
        item = table.item(row, column)
        if item:
            if column == 1:
                item.setIcon(QIcon(abs_path.resource("img/hover_view_icon.png")))
                self.last_hovered = (row, column)
            elif column == 2:
                item.setIcon(QIcon(abs_path.resource("img/hover_edit_icon.png")))
                self.last_hovered = (row, column)
            elif column == 3:
                item.setIcon(QIcon(abs_path.resource("img/hover_delete_icon.png")))
                self.last_hovered = (row, column)

    def msds_cell_clicked(self, row, column):
        msds_id = self.msds_records_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if column == 1:  # view column
            display_text = self.msds_records_table.item(row, 0).text()
            self.open_msds_preview(msds_id, display_text)

        if column == 2:  # edit column
            msds_data_entry.current_msds_id = msds_id  # Store the selected MSDS ID
            msds_data_entry.load_msds_details(self, msds_id)
            # Switch to the MSDS tab
            self.msds_sub_tabs.setCurrentWidget(self.msds_data_entry_tab)
        if column == 3:  # delete column
            confirm = window_alert.show_message(self, "Confirm Deletion",
                                                "Are you sure you want to delete this MSDS record?",
                                                icon_type="question", is_confirmation=True)
            if confirm:
                try:
                    db_con.delete_msds_sheet(msds_id)
                    window_alert.show_message(self, "Deleted", "MSDS record deleted successfully.", icon_type="info")
                except Exception as e:
                    window_alert.show_message(self, "Error", str(e), icon_type="critical")
                finally:
                    table.load_msds_table(self)

    def coa_cell_clicked(self, row, column):
        coa_id = self.coa_records_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        if column == 1:  # view column
            display_text = self.coa_records_table.item(row, 0).text()
            if coa_id in self.all_terumo_id:
                self.open_terumo_preview(coa_id, display_text)
            else:
                self.open_coa_preview(coa_id, display_text)
        if column == 2:  # edit column
            if coa_id in self.all_terumo_id:
                terumo.current_coa_id = coa_id  # Store the selected COA ID
                terumo.load_coa_details(self, coa_id)
                self.coa_sub_tabs.setCurrentWidget(self.coa_data_entry_tab)
                self.coa_data_entry_sub_tabs.setCurrentIndex(1)
            else:
                coa_data_entry.current_coa_id = coa_id
                coa_data_entry.load_coa_details(self, coa_id, self.is_rrf)
                # Switch to the COA tab
                self.coa_sub_tabs.setCurrentWidget(self.coa_data_entry_tab)
                self.coa_data_entry_sub_tabs.setCurrentIndex(0)
        if column == 3:  # delete column
            msg = " - RRF" if self.is_rrf else ""
            confirm = window_alert.show_message(self, "Confirm Deletion",
                                                f"Are you sure you want to delete this Certificate of Analysis{msg} record?",
                                                icon_type="question", is_confirmation=True)
            if confirm:
                try:
                    if self.is_rrf:
                        db_con.delete_certificate_of_analysis_rrf(coa_id)
                        window_alert.show_message(self, "Deleted",
                                                  "Certificate of Analysis - RRF record deleted successfully.",
                                                  icon_type="info")
                        table.load_rrf_table(self)
                    else:
                        db_con.delete_certificate_of_analysis(coa_id)
                        window_alert.show_message(self, "Deleted",
                                                  "Certificate of Analysis record deleted successfully.",
                                                  icon_type="info")
                        table.load_coa_table(self)
                except Exception as e:
                    window_alert.show_message(self, "Error", str(e), icon_type="critical")

    def toggle_msds_search_bar(self, index):
        try:
            if index == 0:  # Records tab
                self.msds_search_bar.show()
                self.msds_search_bar.setFocus()
                msds_data_entry.clear_msds_form(self)
            else:  # Other tabs
                self.msds_search_bar.hide()
                self.msds_scroll_area.verticalScrollBar().setValue(0)
        except Exception as e:
            window_alert.show_message(self, "Unexpected Error", f"An error occurred: {str(e)}", icon_type="critical")

    def toggle_coa_search_bar(self, index):
        try:
            if index == 0:  # Records tab
                self.coa_search_bar.show()
                self.coa_search_bar.setFocus()
                coa_data_entry.clear_coa_form(self)
                terumo.clear_coa_form(self)
            else:
                self.coa_search_bar.hide()
                self.coa_scroll_area.verticalScrollBar().setValue(0)
        except Exception as e:
            window_alert.show_message(self, "Unexpected Error", f"An error occurred: {str(e)}", icon_type="critical")

    def setup_finished_typing(self, line_edit, callback, delay=800):
        timer = QTimer()
        timer.setSingleShot(True)

        # Connect the timer timeout to the callback
        timer.timeout.connect(callback)

        # Restart timer on every text change
        line_edit.textChanged.connect(lambda: timer.start(delay))

        # Optionally return the timer in case you want to manipulate it later
        return timer

    def check_email(self):
        text = self.email_label_input.text()
        validator = self.email_label_input.validator()
        if validator:
            state = validator.validate(text, 0)[0]
            if state != QRegularExpressionValidator.State.Acceptable and text:
                msg = QMessageBox()
                msg.setWindowTitle("Invalid Email")
                msg.setText("❌ Please enter a valid email address!")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.exec()

    def check_tel_number(self):
        if not self.tel_label_input.hasAcceptableInput():
            msg = QMessageBox()
            msg.setWindowTitle("Invalid Telephone Number")
            msg.setText("❌ Please enter a valid telephone number!")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.exec()

    def resize_summary_table(self):
        parent_width = self.coa_data_entry_tab.width()
        table_width = int(parent_width * 0.7)  # 50% width
        self.summary_analysis_table.setFixedWidth(table_width)

    def open_msds_preview(self, msds_id, filename):
        # If the widget already exists, close it first to avoid multiple instances
        if self.msds_widget is not None:
            self.msds_widget.close()
            # It's good practice to deleteLater for QObjects that are not explicitly parented
            # to be garbage collected when they are no longer visible.
            self.msds_widget.deleteLater()
        self.msds_widget = FileMSDS()
        self.msds_widget.show_pdf_preview(msds_id, filename)
        self.msds_widget.resize(900, 800)
        self.msds_widget.show()
        self.msds_widget.activateWindow()
        self.msds_widget.raise_()
        # Bring to front and give focus

    def open_coa_preview(self, coa_id, filename):
        # If the widget already exists, close it first to avoid multiple instances
        if self.coa_widget is not None:
            self.coa_widget.close()
            self.coa_widget.deleteLater()  # Good practice
        self.coa_widget = FileCOA()
        self.coa_widget.show_pdf_preview(coa_id, filename, self.is_rrf)
        self.coa_widget.resize(900, 800)
        self.coa_widget.show()
        self.coa_widget.activateWindow()
        self.coa_widget.raise_()

    def open_terumo_preview(self, coa_id, filename):
        # If the widget already exists, close it first to avoid multiple instances
        if self.terumo_widget is not None:
            self.terumo_widget.close()
            self.terumo_widget.deleteLater()  # Good practice
        self.terumo_widget = FileTerumo()
        self.terumo_widget.show_pdf_preview(coa_id, filename, self.is_rrf)
        self.terumo_widget.resize(900, 800)
        self.terumo_widget.show()
        self.terumo_widget.activateWindow()
        self.terumo_widget.raise_()

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

    def run_sync_script_rrf(self):
        # Show loading dialog
        self.rrf_loading_dialog = LoadingDialog(self)
        self.rrf_loading_dialog.show()

        # Run in a worker thread
        class RRFWorker(QThread):
            sync_finished = pyqtSignal()

            def run(self):
                # Replace with the actual object and method you want to run
                db_rrf.SyncRRFWorker().run()
                self.sync_finished.emit()

        self.rrf_sync_worker = RRFWorker()
        self.rrf_sync_worker.sync_finished.connect(self.rrf_loading_dialog.accept)
        self.rrf_sync_worker.start()

    def logout(self):
        confirm = window_alert.show_message(self, "Logout Confirmation",
                                            "Are you sure you want to log out?",
                                            icon_type="question", is_confirmation=True)
        if confirm:
            self.username = None
            self.close()
            # Re-open the AuthWindow (assuming Login.AuthWindow is your login screen)
            self.auth_window = Login.AuthWindow()
            self.auth_window.show()

    def toggle_rrf(self, checked):
        if checked:
            self.is_rrf = True
            self.btn_switch_rrf.setText("Switch to COA")
            self.btn_switch_rrf.setStyleSheet("""
                QPushButton {
                    background-color: #388E3C;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 12px;
                    margin-bottom: 5px;
                }
                QPushButton:hover { background-color: #2E7D32; }
                QPushButton:pressed { background-color: #1B5E20; }
            """)

            # Load RRF Table
            table.load_rrf_table(self)
            # Remove previous typing connection
            self.coa_label_timer.timeout.disconnect()
            self.delivery_receipt_timer.timeout.disconnect()
            # Connect a new one
            self.coa_label_timer.timeout.connect(
                lambda: table.search_coa_rrf(self, self.coa_search_bar.text())
            )
            self.delivery_receipt_timer.timeout.connect(
                lambda: coa_data_entry.populate_coa_rrf_fields(self, self.delivery_receipt_input.text())
            )

            #Data Entry
            self.coa_header_label.setText("Certificate of Analysis - RRF")
            self.dr_completer.model().setStringList(self.rrf_no_list)
            self.delivery_receipt_label.setText("RRF No:")
            coa_data_entry.clear_coa_form(self)
            terumo.clear_coa_form(self)
            #  change the connected function
            self.coa_data_entry_sub_tabs.setTabEnabled(1, False)
            try:
                self.sync_button.clicked.disconnect()
            except TypeError:
                pass
            # Connect a new function
            self.sync_button.clicked.connect(self.run_sync_script_rrf)

        else:  #back to COA
            self.is_rrf = False
            self.btn_switch_rrf.setText("Switch to RRF")
            self.btn_switch_rrf.setStyleSheet("""
                QPushButton {
                    background-color: #1976D2;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 12px;
                    margin-bottom: 5px;
                }
                QPushButton:hover { background-color: #1565C0; }
                QPushButton:pressed { background-color: #0D47A1; }
            """)
            # Back to COA table
            table.load_coa_table(self)
            self.coa_label_timer.timeout.disconnect()
            self.delivery_receipt_timer.timeout.disconnect()
            # Connect back to original type connection
            self.coa_label_timer.timeout.connect(
                lambda: table.search_coa(self, self.coa_search_bar.text())
            )
            self.delivery_receipt_timer.timeout.connect(
                lambda: coa_data_entry.populate_coa_fields(self, self.delivery_receipt_input.text())
            )

            # Data Entry
            self.coa_header_label.setText("Certificate of Analysis")
            self.dr_completer.model().setStringList(self.dr_no_list)
            self.delivery_receipt_label.setText("Delivery Receipt No:")
            coa_data_entry.clear_coa_form(self)
            terumo.clear_coa_form(self)
            self.coa_data_entry_sub_tabs.setTabEnabled(1, True)
            #  change the connected function
            try:
                self.sync_button.clicked.disconnect()
            except TypeError:
                pass
            # Connect a new function
            self.sync_button.clicked.connect(self.run_sync_script)


class UserWidget(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to fit snugly

        # Username Label
        self.username_label = QLabel(f"Hello, {self.username}!") if self.username is not None else QLabel("Hello!")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.username_label.setFont(font)
        self.username_label.setStyleSheet("color: #333;")
        layout.addWidget(self.username_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Logout Button
        self.logout_button = QPushButton("Logout")
        self.logout_button.setIcon(QIcon(abs_path.resource("img/logout_icon.png")))  # Assuming you have a logout icon
        self.logout_button.setStyleSheet("""
            QPushButton {
                background-color: none; /* Red */
                color: #F44336;
                border: none;
                padding: 5px 10px;
                font-size: 16px;
                margin-left: 10px; /* Space from username */
                margin-right: 20px;
            }
            QPushButton:hover {
                color:white;
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                color:white;
                background-color: #c62828;
            }
        """)
        self.logout_button.clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.logout_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()  # Pushes content to the left (or right if widget is set to the right)


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Syncing...")
        self.setModal(True)  # blocks interaction with main window
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)  # disable close button
        self.setFixedSize(200, 100)

        layout = QVBoxLayout(self)
        self.label = QLabel("Please wait, syncing...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate (infinite loading)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress)