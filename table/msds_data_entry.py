from PyQt6.QtCore import Qt, QObject, QEvent, QTimer
from PyQt6.QtGui import QFontMetrics, QKeySequence, QShortcut
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QWidget, QLineEdit, QPushButton, QTextEdit,
                             QGroupBox, QGridLayout, QInputDialog, QSizePolicy)

from alert import window_alert
from db import db_con
from utils import section2_ui

current_msds_id = None  # Global variable to store the current MSDS ID

LABEL_W = 205           # px, label column of every card
FORM_MAX_W = 1120       # px, the form is centered and never wider than this

# Section 9 defaults (used by the form and by clear_msds_form)
DEFAULT_SECTION9 = [
    ("Appearance", "White pellet form"),
    ("Odor", "Odorless"),
    ("Packaging", "25 kgs."),
    ("Carrier Material", "Polyolefin resin"),
    ("Resin Suitability", "Polyolefin"),
    ("Light fastness (1-8)", ""),
    ("Heat Stability (1-5)", ""),
    ("Non Toxicity", "Non-toxic, colorant contains no heavy metal"),
    ("Flash Point", "N/A"),
    ("Auto Ignition", "N/A"),
    ("Explosion Property", "N/A"),
    ("Solubility (Water)", "Insoluble"),
]

# One stylesheet for the whole form (every section is a white "card" on the page background).
# Empty fields are marked with the dynamic property  class="empty_field".
FORM_STYLE = """
    QWidget#msdsForm { background: transparent; }
    QWidget { font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; color: #343a40; }

    QLabel { font-size: 13px; font-weight: 600; color: #495057; background: transparent; }
    QLabel#mainHeader { font-size: 26px; font-weight: 700; color: #1f3a5f; }
    QLabel#subHeader { font-size: 13px; font-weight: 400; color: #6c757d; }

    QLineEdit, QTextEdit {
        font-size: 13px;
        padding: 6px 10px;
        border: 1px solid #ced4da;
        border-radius: 6px;
        background-color: #ffffff;
        min-height: 22px;
        selection-background-color: #aed6f1;
        color: #343a40;
    }
    QLineEdit:hover, QTextEdit:hover { border: 1px solid #adb5bd; }
    QLineEdit:focus, QTextEdit:focus { border: 1px solid #007bff; background-color: #f2f9ff; }
    QLineEdit[class="empty_field"], QTextEdit[class="empty_field"] {
        border: 1px solid #dc3545;
        background-color: #fff5f5;
    }
    QLineEdit[class="empty_field"]:focus, QTextEdit[class="empty_field"]:focus {
        border: 1px solid #dc3545;
        background-color: #fff0f0;
    }

    QGroupBox {
        font-size: 15px;
        font-weight: 700;
        color: #1f3a5f;
        background-color: #ffffff;
        border: 1px solid #dde3ea;
        border-radius: 10px;
        margin-top: 0px;
        padding-top: 42px;
    }
    QGroupBox::title {
        subcontrol-origin: padding;
        subcontrol-position: top left;
        left: 20px;
        top: 12px;
        padding: 0px;
        color: #1f3a5f;
    }

    QPushButton#HazardToggle {
        background-color: #ffffff;
        color: #495057;
        font-size: 12px;
        font-weight: 600;
        padding: 5px 14px;
        border: 1px solid #ced4da;
        border-radius: 6px;
        min-width: 90px;
    }
    QPushButton#HazardToggle:hover { background-color: #f1f3f5; border: 1px solid #adb5bd; }
    QPushButton#HazardToggle:checked { background-color: #e7f1ff; color: #0056b3; border: 1px solid #7ab3ef; }

    QPushButton#resetButton {
        background-color: #ffffff;
        color: #495057;
        font-size: 13px;
        font-weight: 600;
        padding: 8px 18px;
        border: 1px solid #ced4da;
        border-radius: 8px;
        min-height: 22px;
    }
    QPushButton#resetButton:hover { background-color: #f1f3f5; border: 1px solid #868e96; }
    QPushButton#resetButton:pressed { background-color: #e9ecef; }

    /* Section 9 rows */
    QPushButton#actionButton, QPushButton#actionButton_delete {
        background-color: #ffffff;
        font-size: 12px;
        font-weight: 600;
        padding: 0px 10px;
        min-height: 32px;
        max-height: 32px;
        border-radius: 6px;
    }
    QPushButton#actionButton { color: #495057; border: 1px solid #ced4da; min-width: 32px; max-width: 32px; padding: 0px; }
    QPushButton#actionButton:hover { background-color: #e9ecef; }
    QPushButton#actionButton:disabled { color: #ced4da; background-color: #f8f9fa; }
    QPushButton#actionButton_delete { color: #dc3545; border: 1px solid #f1aeb5; min-width: 64px; }
    QPushButton#actionButton_delete:hover { background-color: #ffebeb; border: 1px solid #dc3545; }
    QPushButton#addPropertyButton {
        background-color: #ffffff;
        color: #007bff;
        font-size: 13px;
        font-weight: 600;
        padding: 6px 18px;
        border: 1px dashed #7ab3ef;
        border-radius: 6px;
        min-height: 22px;
    }
    QPushButton#addPropertyButton:hover { background-color: #e9f5ff; border: 1px solid #007bff; }
    QLabel#propertyColon { font-weight: 700; color: #868e96; }
"""


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
class _AutoHeight(QObject):
    """QTextEdit that is `min_lines` high when short, and grows with its text
    up to `max_lines` (then it scrolls)."""

    def __init__(self, edit, min_lines=2, max_lines=7):
        super().__init__(edit)
        self.edit, self.min_lines, self.max_lines = edit, min_lines, max_lines
        edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        edit.textChanged.connect(self.fit)
        edit.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            QTimer.singleShot(0, self.fit)
        return False

    def fit(self):
        e = self.edit
        vw = e.viewport().width()
        if vw <= 20:  # not laid out yet; the Show event will call us again
            return
        doc = e.document()
        doc.setTextWidth(vw)
        line = QFontMetrics(e.font()).lineSpacing()
        margin = doc.documentMargin() * 2
        content = doc.size().height()
        lo = line * self.min_lines + margin
        hi = line * self.max_lines + margin
        chrome = max(e.height() - e.viewport().height(), 0)  # border + padding
        target = int(min(max(content, lo), hi) + chrome)
        if target != e.height():
            e.setFixedHeight(target)


class _ShowFromStart(QObject):
    """A one-line box that is not being edited shows the START of its text
    (instead of the end, which is where setText() leaves it)."""

    def __init__(self, edit):
        super().__init__(edit)
        self.edit = edit
        edit.textChanged.connect(self.reset)
        edit.installEventFilter(self)

    def reset(self, *_):
        if not self.edit.hasFocus():
            self.edit.setCursorPosition(0)

    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.Type.Show, QEvent.Type.Resize, QEvent.Type.FocusOut):
            QTimer.singleShot(0, self.reset)
        return False


def _wire(widget):
    """Validation (red border when empty) + auto-height for text boxes."""
    if isinstance(widget, QLineEdit):
        widget.textChanged.connect(lambda _t, w=widget: validate_field(w))
        if widget.property("_fromstart") is None:
            widget.setProperty("_fromstart", True)
            _ShowFromStart(widget)
    elif isinstance(widget, QTextEdit):
        widget.textChanged.connect(lambda w=widget: validate_field(w))
        if widget.property("_autoheight") is None:
            widget.setProperty("_autoheight", True)
            _AutoHeight(widget)


def _fit_stack(stack):
    """A QStackedLayout is as tall as its tallest page. Make the hidden pages
    ignore their height so the card shrinks when the short page is shown."""
    cur = stack.currentIndex()
    for i in range(stack.count()):
        w = stack.widget(i)
        pol = w.sizePolicy()
        pol.setVerticalPolicy(QSizePolicy.Policy.Preferred if i == cur else QSizePolicy.Policy.Ignored)
        w.setSizePolicy(pol)
    stack.invalidate()


def _fill_grid(layout, fields):
    """label (right aligned, fixed width)  |  field (stretches)"""
    layout.setHorizontalSpacing(16)
    layout.setVerticalSpacing(12)
    layout.setColumnMinimumWidth(0, LABEL_W)
    layout.setColumnStretch(1, 1)
    for r, (label_text, widget) in enumerate(fields):
        if label_text:
            v = Qt.AlignmentFlag.AlignTop if isinstance(widget, QTextEdit) else Qt.AlignmentFlag.AlignVCenter
            lbl = QLabel(label_text)
            if isinstance(widget, QTextEdit):
                lbl.setContentsMargins(0, 8, 0, 0)       # line up with the first text line
            layout.addWidget(lbl, r, 0, Qt.AlignmentFlag.AlignRight | v)
            layout.addWidget(widget, r, 1)
        else:  # no label: the box spans the whole row
            layout.addWidget(widget, r, 0, 1, 2)
        _wire(widget)


def create_form_group(title, fields):
    group = QGroupBox(title)
    layout = QGridLayout(group)
    layout.setContentsMargins(20, 4, 20, 20)
    if len(fields) == 1 and fields[0][0] == "Details:":
        fields = [("", fields[0][1])]  # single box: the card title already says what it is
    _fill_grid(layout, fields)
    return group


def _page(fields):
    page = QWidget()
    layout = QGridLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    _fill_grid(layout, fields)
    return page


# --------------------------------------------------------------------------
# load / build
# --------------------------------------------------------------------------
def load_msds_details(self, msds_id):
    field_result = db_con.get_single_msds_data(msds_id)

    # inputs variable
    self.customer_name_input.setText(str(field_result[1]))
    self.trade_label_input.setText(str(field_result[2]))
    self.manufactured_label_input.setPlainText(str(field_result[6]))
    self.tel_label_input.setText(str(field_result[7]))
    self.facsimile_label_input.setText(str(field_result[8]))
    self.email_label_input.setText(str(field_result[9]))
    self.composition_input.setPlainText(str(field_result[10]))
    self.hazard_preliminaries_input.setText(str(field_result[11]))
    self.hazard_entry_route_input.setText(str(field_result[12]))
    self.hazard_symptoms_input.setText(str(field_result[13]))
    self.hazard_restrictive_condition_input.setText(str(field_result[14]))
    self.hazard_eyes_input.setText(str(field_result[15]))
    self.hazard_general_note_input.setText(str(field_result[16]))
    self.first_aid_inhalation_input.setText(str(field_result[17]))
    self.first_aid_eyes.setText(str(field_result[18]))
    self.first_aid_skin_input.setText(str(field_result[19]))
    self.first_aid_ingestion_input.setText(str(field_result[20]))
    self.fire_fighting_media_input.setPlainText(str(field_result[21]))
    self.accidental_release_input.setPlainText(str(field_result[22]))
    self.handling_input.setText(str(field_result[23]))
    self.msds_storage_input.setText(str(field_result[24]))
    self.exposure_control_input.setText(str(field_result[25]))
    self.respiratory_protection_input.setText(str(field_result[26]))
    self.hand_protection_input.setText(str(field_result[27]))
    self.eye_protection_input.setText(str(field_result[28]))
    self.skin_protection_input.setText(str(field_result[29]))
    self.stability_reactivity_input.setPlainText(str(field_result[30]))
    self.conditions_to_avoid_input.setText(str(field_result[31]))
    self.materials_to_avoid_input.setText(str(field_result[32]))
    self.hazardous_decomposition_input.setText(str(field_result[33]))
    self.toxicological_input.setPlainText(str(field_result[34]))
    self.ecological_input.setPlainText(str(field_result[35]))
    self.disposal_input.setPlainText(str(field_result[36]))
    self.transport_input.setPlainText(str(field_result[37]))
    self.regulatory_input.setPlainText(str(field_result[38]))
    self.msds_shelf_life_input.setText(str(field_result[39]))
    self.other_input.setPlainText(str(field_result[40]))
    self.btn_msds_submit.setText("Update")
    check_empty_fields(self)  # Call validation after loading data

    if not self.hazard_preliminaries_input.text().strip():
        self.hazard_stacked_layout.setCurrentIndex(1)
        self.hazard_general_note_input.clear()
        self.hazard_single_field_input.setText(str(field_result[16]))
        # section 7
        self.handling_storage_stacked_layout.setCurrentIndex(1)
        self.msds_storage_input.clear()
        self.msds_storage_single_input.setText(str(field_result[24]))
    else:
        self.hazard_stacked_layout.setCurrentIndex(0)
        self.handling_storage_stacked_layout.setCurrentIndex(0)
        self.hazard_single_field_input.clear()
        self.msds_storage_single_input.clear()

    # --- Section 9: Physical & Chemical Properties ---
    if hasattr(self, 'physical_properties_layout'):
        # the last item is the "Add Property" row, so stop before it
        while self.physical_properties_layout.count() > 1:
            item = self.physical_properties_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self.physical_property_rows.clear()

    # [(id, msds_id, property_order, property_name, property_value), ...]
    section9_data = db_con.get_single_msds_section9(msds_id)
    if section9_data:
        for row_data in section9_data:
            row_widget = _create_property_row(self, str(row_data[3]), str(row_data[4]))
            self.physical_properties_layout.insertWidget(self.physical_properties_layout.count() - 1, row_widget)

    # --- Section 2: ingredient breakdown ---
    section2_ui.set_rows(self, [(r[3], r[4], r[5]) for r in db_con.get_single_msds_section2(msds_id)])

    _update_property_buttons(self)
    check_empty_fields(self)


def _ctrl_s(self):
    """Ctrl+S -> behave exactly like a click on Submit / Update."""
    on_msds_entry = (self.main_tabs.currentWidget() is self.msds_tab
                     and self.msds_sub_tabs.currentWidget() is self.msds_data_entry_tab)
    if on_msds_entry and self.btn_msds_submit.isEnabled():
        self.btn_msds_submit.click()


def _reset_button(self):
    btn = QPushButton("↺  New Entry / Reset")
    btn.setObjectName("resetButton")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setToolTip("Put every field back to its default value and start a new entry")
    btn.clicked.connect(lambda: reset_form(self))
    return btn


def reset_form(self):
    """New entry: every field back to its default value (asks first)."""
    confirm = window_alert.show_message(
        self, "New Entry",
        "Reset the form to its default values and start a new entry?\nAnything not submitted yet will be lost.",
        icon_type="question", is_confirmation=True)
    if not confirm:
        return
    clear_msds_form(self)   # also drops the "editing" state, so the next Submit creates a new record
    if hasattr(self, "msds_scroll_area"):
        self.msds_scroll_area.verticalScrollBar().setValue(0)
    self.customer_name_input.setFocus()


def create_form(self):
    clear_msds_form(self)

    form_widget = QWidget()
    form_widget.setObjectName("msdsForm")
    form_widget.setStyleSheet(FORM_STYLE)
    form_widget.setMaximumWidth(FORM_MAX_W)
    main_v_layout = QVBoxLayout(form_widget)
    main_v_layout.setContentsMargins(24, 18, 24, 28)
    main_v_layout.setSpacing(18)

    # Ctrl+S = same as clicking Submit / Update (works anywhere in the window
    # as long as the MSDS "Data Entry" tab is the one on screen)
    save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
    save_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
    save_shortcut.activated.connect(lambda: _ctrl_s(self))
    self.btn_msds_submit.setToolTip("Ctrl+S")

    # === Header ===
    header_box = QVBoxLayout()
    header_box.setSpacing(2)
    header = QLabel("Technical Data and Material Safety")
    header.setObjectName("mainHeader")
    sub = QLabel("Fill in every section. Fields that are still empty are outlined in red.")
    sub.setObjectName("subHeader")
    header_box.addWidget(header)
    header_box.addWidget(sub)
    header_row = QHBoxLayout()
    header_row.addLayout(header_box, 1)
    header_row.addWidget(_reset_button(self), 0, Qt.AlignmentFlag.AlignTop)
    main_v_layout.addLayout(header_row)

    # ---- 1) Product Identification ----
    main_v_layout.addWidget(create_form_group("1) Product Identification", [
        ("Customer Name:", self.customer_name_input),
        ("Trade Name:", self.trade_label_input),
        ("Manufactured By:", self.manufactured_label_input),
        ("Tel No.:", self.tel_label_input),
        ("Facsimile:", self.facsimile_label_input),
        ("Email Address:", self.email_label_input),
    ]))

    # ---- 2) Composition + ingredient breakdown ----
    main_v_layout.addWidget(section2_ui.build_group(self, _wire))

    # ---- 3) Hazard Information (detailed / simplified) ----
    self.hazard_toggle_button = QPushButton("Switch Layout")
    self.hazard_toggle_button.setObjectName("HazardToggle")
    self.hazard_toggle_button.setCheckable(True)
    self.hazard_toggle_button.setChecked(False)  # Start with detailed view
    self.hazard_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)

    detailed_hazard_fields = [
        ("Preliminaries:", self.hazard_preliminaries_input),
        ("Preliminary route of entry:", self.hazard_entry_route_input),
        ("Symptoms of Exposure:", self.hazard_symptoms_input),
        ("Restrictive conditions:", self.hazard_restrictive_condition_input),
        ("Eyes:", self.hazard_eyes_input),
        ("General Note:", self.hazard_general_note_input),
    ]
    self.hazard_stacked_layout.addWidget(_page(detailed_hazard_fields))  # 0
    self.hazard_stacked_layout.addWidget(_page([("General Note:", self.hazard_single_field_input)]))  # 1
    self.hazard_stacked_layout.currentChanged.connect(lambda _i, s=self.hazard_stacked_layout: _fit_stack(s))
    _fit_stack(self.hazard_stacked_layout)

    button_h_layout = QHBoxLayout()
    button_h_layout.addStretch()
    button_h_layout.addWidget(self.hazard_toggle_button)
    self.hazard_group_v_layout.setContentsMargins(20, 4, 20, 20)
    self.hazard_group_v_layout.setSpacing(10)
    self.hazard_group_v_layout.addLayout(button_h_layout)
    self.hazard_group_v_layout.addLayout(self.hazard_stacked_layout)
    main_v_layout.addWidget(self.hazard_group)

    # ---- 4) 5) 6) ----
    main_v_layout.addWidget(create_form_group("4) First Aid Measures", [
        ("Inhalation:", self.first_aid_inhalation_input),
        ("Eyes:", self.first_aid_eyes),
        ("Skin:", self.first_aid_skin_input),
        ("Ingestion:", self.first_aid_ingestion_input),
    ]))
    main_v_layout.addWidget(create_form_group("5) Fire Fighting Measures",
                                              [("Details:", self.fire_fighting_media_input)]))
    main_v_layout.addWidget(create_form_group("6) Accidental Release Measures",
                                              [("Details:", self.accidental_release_input)]))

    # ---- 7) Handling and Storage (detailed / simplified) ----
    self.handling_storage_stacked_layout.addWidget(_page([
        ("Handling:", self.handling_input),
        ("Storage:", self.msds_storage_input),
    ]))  # 0
    self.handling_storage_stacked_layout.addWidget(_page([("Storage:", self.msds_storage_single_input)]))  # 1
    self.handling_storage_stacked_layout.currentChanged.connect(
        lambda _i, s=self.handling_storage_stacked_layout: _fit_stack(s))
    _fit_stack(self.handling_storage_stacked_layout)

    self.handling_storage_group_v_layout.setContentsMargins(20, 4, 20, 20)
    self.handling_storage_group_v_layout.addLayout(self.handling_storage_stacked_layout)
    main_v_layout.addWidget(self.handling_storage_group)

    def toggle_hazard_layout(checked):
        if checked:
            self.hazard_stacked_layout.setCurrentIndex(1)  # Show simplified
            self.hazard_toggle_button.setText("Switch layout")
            self.hazard_single_field_input.setText(
                "No known harmful effects to human lives or to the environment.")

            # Clear all detailed fields except the general note
            for _, input_widget in detailed_hazard_fields:
                if input_widget != self.hazard_general_note_input and hasattr(input_widget, "clear"):
                    input_widget.clear()

            self.hazard_general_note_input.clear()
            # section 7
            self.handling_storage_stacked_layout.setCurrentIndex(1)
            self.handling_input.clear()
            self.msds_storage_input.clear()
            self.msds_storage_single_input.setText(
                "Store in a dry place and shaded area. Close bag after use to prevent moisture intake & soiling.")

        else:
            self.hazard_stacked_layout.setCurrentIndex(0)  # Show detailed
            self.hazard_toggle_button.setText("Switch Layout")
            self.hazard_preliminaries_input.setText("Inert nuisance dust can cause lung irritation.")
            self.hazard_entry_route_input.setText("Inhalation of airborne dust.")
            self.hazard_symptoms_input.setText("Coughing, sneezing or irritation of the mucous membrane.")
            self.hazard_restrictive_condition_input.setText("Breathing or respiratory tract disorder/disease")
            self.hazard_eyes_input.setText("Inert foreign body hazard.")
            self.hazard_general_note_input.setText(
                "No adverse health effects during the course of normal industrial handling. If large quantities ingested, seek medical attention.")

            self.hazard_single_field_input.clear()
            # section 7
            self.handling_storage_stacked_layout.setCurrentIndex(0)
            self.msds_storage_single_input.clear()
            self.handling_input.setText("Use suitable ventilation to prevent excessive inhalation and skin contact. Avoid static discharge during powder handling operation")
            self.msds_storage_input.setText("Store in dry area, wet material may become very slippery. Close bag after use to prevent moisture intake & soiling.")

    self.hazard_toggle_button.clicked.connect(toggle_hazard_layout)

    # ---- 8) .. 17) ----
    main_v_layout.addWidget(create_form_group("8) Exposure Controls/Personal Protection", [
        ("Exposure Control:", self.exposure_control_input),
        ("Respiratory Protection:", self.respiratory_protection_input),
        ("Hand Protection:", self.hand_protection_input),
        ("Eye Protection:", self.eye_protection_input),
        ("Skin Protection:", self.skin_protection_input),
    ]))
    main_v_layout.addWidget(create_dynamic_section9(self))  # 9
    main_v_layout.addWidget(create_form_group("10) Stability && Reactivity", [
        ("", self.stability_reactivity_input),
        ("Conditions to avoid:", self.conditions_to_avoid_input),
        ("Materials to avoid:", self.materials_to_avoid_input),
        ("Hazardous decomposition:", self.hazardous_decomposition_input),
    ]))
    main_v_layout.addWidget(create_form_group("11) Toxicological Information", [("Details:", self.toxicological_input)]))
    main_v_layout.addWidget(create_form_group("12) Ecological Information", [("Details:", self.ecological_input)]))
    main_v_layout.addWidget(create_form_group("13) Disposal", [("Details:", self.disposal_input)]))
    main_v_layout.addWidget(create_form_group("14) Transport Information", [("Details:", self.transport_input)]))
    main_v_layout.addWidget(create_form_group("15) Regulatory Information", [("Details:", self.regulatory_input)]))
    main_v_layout.addWidget(create_form_group("16) Shelf-Life", [("Details:", self.msds_shelf_life_input)]))
    main_v_layout.addWidget(create_form_group("17) Other Information", [("Details:", self.other_input)]))

    main_v_layout.addLayout(form_btn(self))
    main_v_layout.addStretch(1)

    # centered column, never wider than FORM_MAX_W
    outer = QHBoxLayout()
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addStretch(1)
    outer.addWidget(form_widget, 100)
    outer.addStretch(1)
    self.msds_form_layout.addLayout(outer)

    # Perform initial validation after all widgets are set up
    check_empty_fields(self)


def create_dynamic_section9(self):
    """Custom dynamic layout for Section 9."""
    group = QGroupBox("9) Physical && Chemical Properties")
    group.setObjectName("section9Group")
    self.physical_properties_layout = QVBoxLayout()
    self.physical_properties_layout.setContentsMargins(20, 4, 20, 20)
    self.physical_properties_layout.setSpacing(8)
    self.physical_property_rows = []  # Reset for cleanliness

    for name, value in DEFAULT_SECTION9:
        self.physical_properties_layout.addWidget(_create_property_row(self, name, value))

    # Add button row at the bottom
    add_row = QWidget()
    add_hlayout = QHBoxLayout(add_row)
    add_hlayout.setContentsMargins(0, 6, 0, 0)
    add_btn = QPushButton("+ Add Property")
    add_btn.setObjectName("addPropertyButton")
    add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    add_btn.clicked.connect(lambda: _add_property(self))
    add_hlayout.addWidget(add_btn)
    add_hlayout.addStretch()
    self.physical_properties_layout.addWidget(add_row)

    _update_property_buttons(self)

    group.setLayout(self.physical_properties_layout)
    return group


def _create_property_row(self, name, value):
    """Create a single dynamic row widget:  [name]  :  [value]  [↑] [↓] [Delete]"""
    row_widget = QWidget()
    row_layout = QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(8)

    name_edit = QLineEdit(name)
    name_edit.setObjectName("propertyName")
    name_edit.setMinimumWidth(180)
    value_edit = QLineEdit(value)
    value_edit.setProperty("class", "")
    colon = QLabel(":")
    colon.setObjectName("propertyColon")
    delete_btn = QPushButton("Delete")
    delete_btn.setObjectName("actionButton_delete")
    delete_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    up_btn = QPushButton("↑")
    up_btn.setObjectName("actionButton")
    up_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    down_btn = QPushButton("↓")
    down_btn.setObjectName("actionButton")
    down_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    row_layout.addWidget(name_edit, stretch=2)
    row_layout.addWidget(colon)
    row_layout.addWidget(value_edit, stretch=3)
    row_layout.addWidget(up_btn)
    row_layout.addWidget(down_btn)
    row_layout.addWidget(delete_btn)

    # Store references on row_widget for easy access
    row_widget.name_edit = name_edit
    row_widget.value_edit = value_edit
    row_widget.up_btn = up_btn
    row_widget.down_btn = down_btn
    row_widget.delete_btn = delete_btn

    # Track in order list
    self.physical_property_rows.append((name_edit, value_edit))

    name_edit.textChanged.connect(lambda: validate_field(name_edit))
    value_edit.textChanged.connect(lambda: validate_field(value_edit))

    def delete_row():
        idx = self.physical_properties_layout.indexOf(row_widget)
        if idx != -1 and idx < self.physical_properties_layout.count() - 1:  # Not the add row
            self.physical_properties_layout.removeWidget(row_widget)
            row_widget.deleteLater()
            self.physical_property_rows.remove((name_edit, value_edit))
            _update_property_buttons(self)

    def move_up():
        idx = self.physical_properties_layout.indexOf(row_widget)
        if idx > 0 and idx < self.physical_properties_layout.count() - 1:
            self.physical_properties_layout.removeWidget(row_widget)
            self.physical_properties_layout.insertWidget(idx - 1, row_widget)
            for i, t in enumerate(self.physical_property_rows):
                if t[0] == name_edit:
                    if i > 0:
                        self.physical_property_rows[i], self.physical_property_rows[i - 1] = \
                            self.physical_property_rows[i - 1], self.physical_property_rows[i]
                    break
            _update_property_buttons(self)

    def move_down():
        idx = self.physical_properties_layout.indexOf(row_widget)
        total_rows = self.physical_properties_layout.count() - 1  # Exclude add row
        if 0 <= idx < total_rows - 1:
            self.physical_properties_layout.removeWidget(row_widget)
            self.physical_properties_layout.insertWidget(idx + 1, row_widget)
            for i, t in enumerate(self.physical_property_rows):
                if t[0] == name_edit:
                    if i < len(self.physical_property_rows) - 1:
                        self.physical_property_rows[i], self.physical_property_rows[i + 1] = \
                            self.physical_property_rows[i + 1], self.physical_property_rows[i]
                    break
            _update_property_buttons(self)

    delete_btn.clicked.connect(delete_row)
    up_btn.clicked.connect(move_up)
    down_btn.clicked.connect(move_down)

    return row_widget


def _add_property(self):
    """Add a new empty row."""
    name, ok = QInputDialog.getText(self, "Add Property", "Property Name:", text="")
    if ok and name.strip():
        row = _create_property_row(self, name.strip(), "")
        self.physical_properties_layout.insertWidget(self.physical_properties_layout.count() - 1, row)
        _update_property_buttons(self)


def _update_property_buttons(self):
    """Enable/disable up/down buttons based on position."""
    total_rows = self.physical_properties_layout.count() - 1  # Exclude add row
    for i in range(total_rows):
        item = self.physical_properties_layout.itemAt(i)
        if item and item.widget():
            row_widget = item.widget()
            if hasattr(row_widget, 'up_btn'):
                row_widget.up_btn.setEnabled(i > 0)
                row_widget.down_btn.setEnabled(i < total_rows - 1)


def form_btn(self):
    button_style = """
        QPushButton {
            background-color: #007bff;
            color: #ffffff;
            font-size: 15px;
            font-weight: 600;
            padding: 8px 28px;
            border: none;
            border-radius: 8px;
            min-width: 150px;
            min-height: 26px;
        }
        QPushButton:hover { background-color: #0056b3; }
        QPushButton:pressed { background-color: #004085; }
        QPushButton:focus { outline: none; border: 2px solid #5dade2; }
    """
    self.btn_msds_submit.setStyleSheet(button_style)
    self.btn_msds_submit.setCursor(Qt.CursorShape.PointingHandCursor)
    submit_button_row = QHBoxLayout()
    submit_button_row.setSpacing(12)
    submit_button_row.addStretch()
    submit_button_row.addWidget(_reset_button(self))
    submit_button_row.addWidget(self.btn_msds_submit)
    submit_button_row.addStretch()  # Center buttons
    return submit_button_row


def clear_msds_form(self):
    """Reset every field to its default text."""
    global current_msds_id
    try:
        current_msds_id = None  # Reset the global MSDS ID

        # Stop all typing timers (assuming these exist and are QTimer objects)
        if hasattr(self, 'tel_label_timer') and self.tel_label_timer.isActive():
            self.tel_label_timer.stop()
        if hasattr(self, 'facsimile_label_timer') and self.facsimile_label_timer.isActive():
            self.facsimile_label_timer.stop()
        if hasattr(self, 'email_label_timer') and self.email_label_timer.isActive():
            self.email_label_timer.stop()

        self.manufactured_label_input.setPlainText(
            "Masterbatch Philippines, Inc. 24 Diamond Road, Caloocan Industrial Subdivision, Bo. Kaybiga, Caloocan City, Philippines")
        self.tel_label_input.setText("(632) 70023720")
        self.facsimile_label_input.setText("(63) 9088106546")
        self.email_label_input.setText("sales@polycolor.biz")
        self.composition_input.setPlainText(
            "The preparation consists of organic and inorganic pigments, and other additives.")
        self.hazard_preliminaries_input.setText("Inert nuisance dust can cause lung irritation.")
        self.hazard_entry_route_input.setText("Inhalation of airborne dust.")
        self.hazard_symptoms_input.setText("Coughing, sneezing or irritation of the mucous membrane.")
        self.hazard_restrictive_condition_input.setText("Breathing or respiratory tract disorder/disease")
        self.hazard_eyes_input.setText("Inert foreign body hazard.")
        self.hazard_general_note_input.setText(
            "No adverse health effects during the course of normal industrial handling. If large quantities ingested, seek medical attention.")
        self.first_aid_inhalation_input.setText("Remove to fresh air.")
        self.first_aid_eyes.setText("Flush with large amount of water. If irritation persists, seek medical attention.")
        self.first_aid_skin_input.setText("Wash with mild soap")
        self.first_aid_ingestion_input.setText(
            "No adverse health effects during the course of normal industrial handling. If large quantities ingested, seek medical attention.")
        self.fire_fighting_media_input.setPlainText("Water spray, dry powder, foam, carbon dioxide")
        self.accidental_release_input.setPlainText(
            "Use any mechanical means to remove pellet. Prevent entry to natural waterways.")
        self.handling_input.setText(
            "Use suitable ventilation to prevent excessive inhalation and skin contact. Avoid static discharge during powder handling operation.")
        self.msds_storage_input.setText(
            "Store in dry area, wet material may become very slippery. Close bag after use to prevent moisture intake & soiling.")
        self.exposure_control_input.setText(
            "Generally handle in areas of good ventilation. If airborne dust is over or thought to approach the occupational exposure standard, local exhaust may be necessary.")
        self.respiratory_protection_input.setText(
            "Use approved dust respirator if occupational exposure standard is likely to be exceeded.")
        self.hand_protection_input.setText("Use gloves for prolonged/repeated contact.")
        self.eye_protection_input.setText("Use safety glasses/ goggles.")
        self.skin_protection_input.setText(
            "Wear normal protective overalls. Sensitive skin can be protected further by use of barrier cream or moisturizer.")

        # Reset Section 9 to initials
        if hasattr(self, 'physical_properties_layout'):
            while self.physical_properties_layout.count() > 1:  # Keep add row
                item = self.physical_properties_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.physical_property_rows.clear()

            for name, value in DEFAULT_SECTION9:
                row = _create_property_row(self, name, value)
                self.physical_properties_layout.insertWidget(self.physical_properties_layout.count() - 1, row)
            _update_property_buttons(self)

        section2_ui.set_rows(self, [])

        # back to the detailed Hazard (3) / Handling & Storage (7) layout
        if hasattr(self, "hazard_toggle_button"):
            self.hazard_stacked_layout.setCurrentIndex(0)
            self.handling_storage_stacked_layout.setCurrentIndex(0)
            self.hazard_toggle_button.setChecked(False)
            self.hazard_toggle_button.setText("Switch Layout")
            self.hazard_single_field_input.clear()
            self.msds_storage_single_input.clear()

        self.stability_reactivity_input.setPlainText("This product is chemically stable and non-reactive.")
        self.conditions_to_avoid_input.setText("None")
        self.materials_to_avoid_input.setText("None")
        self.hazardous_decomposition_input.setText("None")
        self.toxicological_input.setPlainText("This product is non-toxic and physiologically harmless.")
        self.ecological_input.setPlainText("No known harmful effects to human lives or to the environment.")
        self.disposal_input.setPlainText(
            "If recycling is not practicable, dispose in compliance with local regulation.")
        self.transport_input.setPlainText(
            "This material is not classified as a dangerous good by International Transport regulation.")
        self.regulatory_input.setPlainText(
            "This product is not classified in the list of controlled substances implemented by the government.")
        self.msds_shelf_life_input.setPlainText(
            "Twelve months from date of production when the product is stored in unbroken packaging.")
        self.other_input.setPlainText("None")

        # Clear QLineEdit/QTextEdit fields
        for widget in [
            self.customer_name_input,
            self.trade_label_input,
        ]:
            widget.blockSignals(True)
            widget.clear()
            widget.blockSignals(False)
            # Ensure the "empty_field" class is removed if it was present
            if widget.property("class") == "empty_field":
                widget.setProperty("class", "")
                widget.style().polish(widget)

        self.btn_msds_submit.setText("Submit")
        check_empty_fields(self)  # Re-validate all fields after clearing
    except Exception as e:
        window_alert.show_message(self, "Unexpected Error", f"An error occurred: {str(e)}", icon_type="critical")


def validate_field(widget):
    """Checks if a QLineEdit or QTextEdit is empty and applies/removes the red border."""
    is_empty = False
    if isinstance(widget, QLineEdit):
        is_empty = not widget.text().strip()
    elif isinstance(widget, QTextEdit):
        is_empty = not widget.toPlainText().strip()

    if is_empty:
        if widget.property("class") != "empty_field":
            widget.setProperty("class", "empty_field")
            widget.style().polish(widget)  # Reapply stylesheet to update appearance
    else:
        if widget.property("class") == "empty_field":
            widget.setProperty("class", "")
            widget.style().polish(widget)  # Reapply stylesheet to update appearance


def check_empty_fields(self):
    """Applies validation to all relevant input fields in the form."""
    input_fields = [
        self.customer_name_input, self.trade_label_input, self.manufactured_label_input,
        self.tel_label_input, self.facsimile_label_input, self.email_label_input,
        self.composition_input, self.hazard_preliminaries_input, self.hazard_entry_route_input,
        self.hazard_symptoms_input, self.hazard_restrictive_condition_input, self.hazard_eyes_input,
        self.hazard_general_note_input, self.first_aid_inhalation_input, self.first_aid_eyes,
        self.first_aid_skin_input, self.first_aid_ingestion_input, self.fire_fighting_media_input,
        self.accidental_release_input, self.handling_input, self.msds_storage_input,
        self.exposure_control_input, self.respiratory_protection_input, self.hand_protection_input,
        self.eye_protection_input, self.skin_protection_input, self.stability_reactivity_input,
        self.conditions_to_avoid_input, self.materials_to_avoid_input, self.hazardous_decomposition_input,
        self.toxicological_input, self.ecological_input, self.disposal_input,
        self.transport_input, self.regulatory_input, self.msds_shelf_life_input,
        self.other_input
    ]

    for field in input_fields:
        validate_field(field)

    for _, value_edit in self.physical_property_rows:
        validate_field(value_edit)