from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QTabWidget, \
    QTableWidget, QLineEdit, QHeaderView, QTableWidgetItem, QFormLayout, QPushButton, QTextEdit, QGroupBox, QGridLayout, \
    QStackedLayout, QInputDialog
from PyQt6.QtCore import Qt  # Import Qt for alignment flags

# Assuming alert and db_con are correctly imported
from alert import window_alert
from db import db_con
from utils import section9_design

current_msds_id = None  # Global variable to store the current MSDS ID


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
    # 1. Clear existing dynamic rows
    if hasattr(self, 'physical_properties_layout'):
        # Iterate backwards to safely remove widgets
        # The last widget is the "Add Property" button, so we stop before it.
        while self.physical_properties_layout.count() > 1:
            item = self.physical_properties_layout.takeAt(0)  # Take the first item (a row widget)
            if item and item.widget():
                item.widget().deleteLater()  # Delete the widget
        self.physical_property_rows.clear()  # Clear the tracking list

    # It should return a list of tuples: [(id, msds_id, property_order, property_name, property_value), ...]
    section9_data = db_con.get_single_msds_section9(msds_id)

    # 3. Create new rows based on fetched data
    if section9_data:
        for row_data in section9_data:
            # Assuming row_data is (id, msds_id, property_order, property_name, property_value)
            property_name = str(row_data[3])
            property_value = str(row_data[4])
            row_widget = _create_property_row(self, property_name, property_value)
            # Insert before the "Add Property" button (which is always the last item)
            self.physical_properties_layout.insertWidget(self.physical_properties_layout.count() - 1, row_widget)

    # 4. Update the state of the up/down buttons
    _update_property_buttons(self)
    check_empty_fields(self)


def create_form(self):
    clear_msds_form(self)

    form_widget = QWidget()
    main_v_layout = QVBoxLayout(form_widget)  # Use QVBoxLayout for overall structure
    main_v_layout.setContentsMargins(30, 20, 30, 30)  # Add overall padding

    form_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa; /* Very light background for the whole form */
                font-family: 'Inter', 'Segoe UI', sans-serif; /* Modern font */
                color: #343a40; /* Dark gray for general text */
            }
            QLabel {
                font-size: 12px; /* Changed from 14px to 12px */
                font-weight: 600;
                color: #495057; /* Slightly darker gray for labels */
                padding-bottom: 2px; /* Small padding below labels */
                background-color: transparent;
            }
            /* Specific style for the main header */
            QLabel#mainHeader {
                font-size: 32px;
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 30px;
                padding-bottom: 10px;
                border-bottom: 3px solid #007bff; /* Primary blue underline */
                text-align: center; /* This will center the text if the label's width allows */
            }
            QLineEdit, QTextEdit {
                font-size: 12px;
                padding: 4px 8px;
                border: 1px solid #ced4da; /* Lighter, more neutral border */
                border-radius: 6px; /* Slightly less rounded for a crisp look */
                background-color: #ffffff;
                min-height: 26px; /* Consistent height for QLineEdit */
                selection-background-color: #aed6f1;
                color: #343a40;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #007bff; /* Primary blue on focus */
                background-color: #e9f5ff; /* Very light blue background on focus */
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25); /* Subtle focus ring */
            }
            /* Style for empty fields with red border */
            QLineEdit.empty_field, QTextEdit.empty_field {
                border: 1px solid #dc3545; /* Red border */
                background-color: #ffebeb; /* Very light red background */
            }
            QLineEdit.empty_field:focus, QTextEdit.empty_field:focus {
                border: 1px solid #dc3545; /* Keep red border on focus for empty fields */
                box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.25); /* Red focus ring */
            }
            QTextEdit {
                min-height: 50px; /* Slightly taller */
                max-height: 80px; /* Allow more vertical space if needed but cap */
                vertical-align: top;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #212529;
                border: 1px solid #e0e0e0; /* Lighter border for group box */
                border-radius: 8px;
                margin-top: 2.0ex; /* Space for title */
                background-color: #ffffff;
                padding: 8px; /* Inner padding for group box content */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px; /* Wider padding for title text */
                left: 15px; /* Adjust title position */
                margin-left: 0px; /* No margin here, padding takes over */
                color: #34495e;
            }
            QPushButton#HazardToggle {
                background-color: #6c757d; /* A neutral gray */
                color: #ffffff;
                font-size: 13px;
                padding: 5px 10px;
                border: none;
                border-radius: 4px;
                min-width: 80px;
                margin-bottom: 10px;
            }
            QPushButton#HazardToggle:hover {
                background-color: #5a6268;
            }
            #detailedHazardWidget, #simplifiedHazardWidget, #detailedHandlingStorageWidget, #simplifiedHandlingStorageWidget {
                background-color: #ffffff;
            }
        """)

    # === Header ===
    header = QLabel("Technical Data and Material Safety")
    header.setObjectName("mainHeader")  # Set object name for styling
    header_layout = QHBoxLayout()
    header_layout.addStretch()
    header_layout.addWidget(header)
    header_layout.addStretch()
    main_v_layout.addLayout(header_layout)  # Add header to the main layout

    # Helper function to create form groups with GridLayout for alignment
    def create_form_group(title, fields):
        group = QGroupBox(title)
        if title == "10) Stability & Reactivity":
            # Use QHBoxLayout for a single row with two sections
            main_layout = QHBoxLayout()
            main_layout.setContentsMargins(20, 25, 20, 20)
            main_layout.setSpacing(30)

            # Left side: Details (QTextEdit, no label)
            details_layout = QVBoxLayout()
            details_widget = fields[0][1]  # self.stability_reactivity_input (QTextEdit)
            details_layout.addWidget(details_widget)
            main_layout.addLayout(details_layout, stretch=2)  # Give more space to Details

            # Right side: Three QLineEdit fields in a vertical layout
            right_layout = QVBoxLayout()
            right_layout.setSpacing(15)
            for label_text, input_widget in fields[1:]:  # Skip Details
                field_layout = QHBoxLayout()
                label = QLabel(label_text)
                field_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                field_layout.addWidget(input_widget)
                right_layout.addLayout(field_layout)
                # Connect text changed signal for validation
                if isinstance(input_widget, QLineEdit):
                    input_widget.textChanged.connect(lambda text, widget=input_widget: validate_field(widget))
            main_layout.addLayout(right_layout, stretch=1)

            group.setLayout(main_layout)
        else:
            # Original single-column layout for other sections
            layout = QGridLayout()
            layout.setHorizontalSpacing(30)
            layout.setVerticalSpacing(15)
            layout.setContentsMargins(20, 25, 20, 20)
            row_idx = 0
            for label_text, input_widget in fields:
                if label_text:  # Only create and add label if label_text is non-empty
                    label = QLabel(label_text)
                    layout.addWidget(label, row_idx, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    layout.addWidget(input_widget, row_idx, 1)
                else:
                    # If no label, span the widget across both columns
                    layout.addWidget(input_widget, row_idx, 0, 1, 2)
                # Connect text changed signal for validation
                if isinstance(input_widget, QLineEdit):
                    input_widget.textChanged.connect(lambda text, widget=input_widget: validate_field(widget))
                elif isinstance(input_widget, QTextEdit):
                    input_widget.textChanged.connect(lambda: validate_field(input_widget))
                row_idx += 1
            group.setLayout(layout)
        return group

    # Section 1: Product Identification
    product_id_fields = [
        ("Customer Name:", self.customer_name_input),
        ("Trade Name:", self.trade_label_input),
        ("Manufactured By:", self.manufactured_label_input),
        ("Tel No.:", self.tel_label_input),
        ("Facsimile:", self.facsimile_label_input),
        ("Email Address:", self.email_label_input),
    ]
    main_v_layout.addWidget(create_form_group("1) Product Identification", product_id_fields))

    # Section 2: Composition/Information on Ingredients
    composition_fields = [
        ("Details:", self.composition_input),
    ]
    main_v_layout.addWidget(create_form_group("2) Composition/Information on Ingredients", composition_fields))

    # Section 3: Hazard Information
    self.hazard_toggle_button = QPushButton("Switch Layout")
    self.hazard_toggle_button.setObjectName("HazardToggle")  # For specific styling
    self.hazard_toggle_button.setCheckable(True)  # Make it checkable for state management
    self.hazard_toggle_button.setChecked(False)  # Start with detailed view

    # Detailed Hazard Fields
    detailed_hazard_fields = [
        ("Preliminaries:", self.hazard_preliminaries_input),
        ("Preliminary route of entry:", self.hazard_entry_route_input),
        ("Symptoms of Exposure:", self.hazard_symptoms_input),
        ("Restrictive conditions:", self.hazard_restrictive_condition_input),
        ("Eyes:", self.hazard_eyes_input),
        ("General Note:", self.hazard_general_note_input),
    ]
    # Simplified Hazard Field (only General Note)
    simplified_hazard_fields = [
        ("General Note:", self.hazard_single_field_input),  # Reuse the same input widget
    ]

    # Create the detailed view widget
    detailed_hazard_widget = QWidget()
    detailed_hazard_widget.setObjectName("detailedHazardWidget")  # Set object name for styling
    detailed_hazard_layout = QGridLayout(detailed_hazard_widget)
    detailed_hazard_layout.setHorizontalSpacing(30)
    detailed_hazard_layout.setVerticalSpacing(15)
    detailed_hazard_layout.setContentsMargins(20, 10, 20, 20)
    row_idx = 0
    for label_text, input_widget in detailed_hazard_fields:
        label = QLabel(label_text)
        detailed_hazard_layout.addWidget(label, row_idx, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        detailed_hazard_layout.addWidget(input_widget, row_idx, 1)
        if isinstance(input_widget, QLineEdit):
            input_widget.textChanged.connect(lambda text, widget=input_widget: validate_field(widget))
        elif isinstance(input_widget, QTextEdit):
            input_widget.textChanged.connect(lambda: validate_field(input_widget))
        row_idx += 1

    # Create the simplified view widget
    simplified_hazard_widget = QWidget()
    simplified_hazard_widget.setObjectName("simplifiedHazardWidget")  # Set object name for styling
    simplified_hazard_layout = QGridLayout(simplified_hazard_widget)
    simplified_hazard_layout.setHorizontalSpacing(30)
    simplified_hazard_layout.setVerticalSpacing(15)
    simplified_hazard_layout.setContentsMargins(20, 10, 20, 20)
    label_general_note = QLabel("General Note:")
    simplified_hazard_layout.addWidget(label_general_note, 0, 0,
                                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    simplified_hazard_layout.addWidget(self.hazard_single_field_input, 0, 1)

    # Create a QStackedLayout for hazard information
    self.hazard_stacked_layout.addWidget(detailed_hazard_widget)  # Index 0: Detailed view
    self.hazard_stacked_layout.addWidget(simplified_hazard_widget)  # Index 1: Simplified view

    button_h_layout = QHBoxLayout()
    button_h_layout.addStretch()
    button_h_layout.addWidget(self.hazard_toggle_button)
    self.hazard_group_v_layout.addLayout(button_h_layout)
    self.hazard_group_v_layout.addLayout(self.hazard_stacked_layout)

    main_v_layout.addWidget(self.hazard_group)

    # Section 4: First Aid Measures
    first_aid_fields = [
        ("Inhalation:", self.first_aid_inhalation_input),
        ("Eyes:", self.first_aid_eyes),
        ("Skin:", self.first_aid_skin_input),
        ("Ingestion:", self.first_aid_ingestion_input),
    ]
    main_v_layout.addWidget(create_form_group("4) First Aid Measures", first_aid_fields))

    # Section 5: Fire Fighting Measures
    fire_fighting_fields = [
        ("Details:", self.fire_fighting_media_input),
    ]
    main_v_layout.addWidget(create_form_group("5) Fire Fighting Measures", fire_fighting_fields))

    # Section 6: Accidental Release Measures
    accidental_release_fields = [
        ("Details:", self.accidental_release_input),
    ]
    main_v_layout.addWidget(create_form_group("6) Accidental Release Measures", accidental_release_fields))

    # Section 7: Handling and Storage - NEW STACKED LAYOUT
    detailed_handling_storage_fields = [
        ("Handling:", self.handling_input),
        ("Storage:", self.msds_storage_input),
    ]

    # Create the detailed handling/storage view widget
    detailed_handling_storage_widget = QWidget()
    detailed_handling_storage_widget.setObjectName("detailedHandlingStorageWidget")
    detailed_handling_storage_layout = QGridLayout(detailed_handling_storage_widget)
    detailed_handling_storage_layout.setHorizontalSpacing(30)
    detailed_hazard_layout.setVerticalSpacing(15)
    detailed_handling_storage_layout.setContentsMargins(20, 10, 20, 20)
    row_idx = 0
    for label_text, input_widget in detailed_handling_storage_fields:
        label = QLabel(label_text)
        detailed_handling_storage_layout.addWidget(label, row_idx, 0,
                                                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        detailed_handling_storage_layout.addWidget(input_widget, row_idx, 1)
        if isinstance(input_widget, QLineEdit):
            input_widget.textChanged.connect(lambda text, widget=input_widget: validate_field(widget))
        elif isinstance(input_widget, QTextEdit):
            input_widget.textChanged.connect(lambda: validate_field(input_widget))
        row_idx += 1

    # Create the simplified handling/storage view widget (only Storage)
    simplified_handling_storage_widget = QWidget()
    simplified_handling_storage_widget.setObjectName("simplifiedHandlingStorageWidget")
    simplified_handling_storage_layout = QGridLayout(simplified_handling_storage_widget)
    simplified_handling_storage_layout.setHorizontalSpacing(30)
    simplified_handling_storage_layout.setVerticalSpacing(15)
    simplified_handling_storage_layout.setContentsMargins(20, 10, 20, 20)
    label_storage_simplified = QLabel("Storage:")
    simplified_handling_storage_layout.addWidget(label_storage_simplified, 0, 0,
                                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    simplified_handling_storage_layout.addWidget(self.msds_storage_single_input, 0, 1)
    if isinstance(self.msds_storage_input, QLineEdit):
        self.msds_storage_input.textChanged.connect(
            lambda text, widget=self.msds_storage_input: validate_field(widget))
    elif isinstance(self.msds_storage_input, QTextEdit):
        self.msds_storage_input.textChanged.connect(lambda: validate_field(self.msds_storage_input))

    self.handling_storage_stacked_layout.addWidget(detailed_handling_storage_widget)  # Index 0: Detailed view
    self.handling_storage_stacked_layout.addWidget(simplified_handling_storage_widget)  # Index 1: Simplified view

    self.handling_storage_group_v_layout.addLayout(self.handling_storage_stacked_layout)
    main_v_layout.addWidget(self.handling_storage_group)

    def toggle_hazard_layout(checked):
        if checked:
            self.hazard_stacked_layout.setCurrentIndex(1)  # Show simplified
            self.hazard_toggle_button.setText("Show Detailed")
            self.hazard_single_field_input.setText(
                "No known harmful effects to human lives or to the environment.")

            # Clear and disable all detailed fields except the general note
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

    # Section 8: Exposure Controls/Personal Protection
    exposure_control_fields = [
        ("Exposure Control:", self.exposure_control_input),
        ("Respiratory Protection:", self.respiratory_protection_input),
        ("Hand Protection:", self.hand_protection_input),
        ("Eye Protection:", self.eye_protection_input),
        ("Skin Protection:", self.skin_protection_input),
    ]
    main_v_layout.addWidget(create_form_group("8) Exposure Controls/Personal Protection", exposure_control_fields))

    # Section 9: Physical & Chemical Properties
    main_v_layout.addWidget(create_dynamic_section9(self))

    # Section 10: Stability & Reactivity
    stability_reactivity_fields = [
        ("", self.stability_reactivity_input),
        ("Conditions to avoid:", self.conditions_to_avoid_input),
        ("Materials to avoid:", self.materials_to_avoid_input),
        ("Hazardous decomposition:", self.hazardous_decomposition_input),
    ]
    main_v_layout.addWidget(create_form_group("10) Stability & Reactivity", stability_reactivity_fields))

    # Section 11: Toxicological Information
    toxicological_fields = [
        ("Details:", self.toxicological_input),
    ]
    main_v_layout.addWidget(create_form_group("11) Toxicological Information", toxicological_fields))

    # Section 12-17
    ecological_fields = [("Details:", self.ecological_input)]
    main_v_layout.addWidget(create_form_group("12) Ecological Information", ecological_fields))

    disposal_fields = [("Details:", self.disposal_input)]
    main_v_layout.addWidget(create_form_group("13) Disposal", disposal_fields))

    transport_fields = [("Details:", self.transport_input)]
    main_v_layout.addWidget(create_form_group("14) Transport Information", transport_fields))

    regulatory_fields = [("Details:", self.regulatory_input)]
    main_v_layout.addWidget(create_form_group("15) Regulatory Information", regulatory_fields))

    shelf_life_fields = [("Details:", self.msds_shelf_life_input)]
    main_v_layout.addWidget(create_form_group("16) Shelf-Life", shelf_life_fields))

    other_info_fields = [("Details:", self.other_input)]
    main_v_layout.addWidget(create_form_group("17) Other Information", other_info_fields))

    main_v_layout.addLayout(form_btn(self))
    main_v_layout.addStretch(1)

    self.msds_form_layout.addWidget(form_widget)

    # Perform initial validation after all widgets are set up
    check_empty_fields(self)

def create_dynamic_section9(self):
    """Custom dynamic layout for Section 9."""
    group = QGroupBox("9) Physical & Chemical Properties")
    group.setObjectName("section9Group")
    self.physical_properties_layout = QVBoxLayout()
    self.physical_property_rows = []  # Reset for cleanliness
    group.setStyleSheet(section9_design.STYLESHEET)

    # Initial fixed properties with defaults (from your clear_msds_form)
    initial_props = [
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

    for name, value in initial_props:
        row = _create_property_row(self, name, value)
        self.physical_properties_layout.addWidget(row)

    # Add button row at the bottom
    add_row = QWidget()
    add_hlayout = QHBoxLayout(add_row)
    add_hlayout.setContentsMargins(20, 10, 20, 10)
    add_btn = QPushButton("Add Property")
    add_btn.setObjectName("addPropertyButton")
    add_btn.clicked.connect(lambda: _add_property(self))
    add_hlayout.addWidget(add_btn)
    add_hlayout.addStretch()
    self.physical_properties_layout.addWidget(add_row)

    # Initial button state update
    _update_property_buttons(self)

    group.setLayout(self.physical_properties_layout)
    return group

def _create_property_row(self, name, value):
    """Create a single dynamic row widget."""
    row_widget = QWidget()
    row_layout = QHBoxLayout(row_widget)
    row_layout.setContentsMargins(20, 10, 20, 10)

    name_edit = QLineEdit(name)
    name_edit.setObjectName("propertyName")
    value_edit = QLineEdit(value)
    value_edit.setProperty("class", "")
    delete_btn = QPushButton("Delete")
    delete_btn.setObjectName("actionButton_delete")
    delete_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    up_btn = QPushButton("↑")
    up_btn.setObjectName("actionButton")
    up_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    down_btn = QPushButton("↓")
    down_btn.setObjectName("actionButton")
    down_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    # Layout: Property: [name] : [value (stretch)] [↑] [↓] [Delete]
    label = QLabel("")
    label.setObjectName("propertyLabel")
    row_layout.addWidget(label)
    row_layout.addWidget(name_edit, stretch=1)
    row_layout.addWidget(QLabel(":"))
    row_layout.addWidget(value_edit, stretch=2)
    row_layout.addStretch()
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

    # Connect validation (reuse your existing function)
    name_edit.textChanged.connect(lambda: validate_field(name_edit))
    value_edit.textChanged.connect(lambda: validate_field(value_edit))

    # Button connections
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
            background-color: #007bff; /* Primary blue for submit (consistent with COA) */
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            min-width: 80px;
            min-height: 30px;
            margin-top: 20px;
            letter-spacing: 0.5px;
        }
        QPushButton:hover {
            background-color: #0056b3; /* Darker blue on hover */
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        QPushButton:pressed {
            background-color: #004085; /* Even darker on press */
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        QPushButton:focus {
            outline: none;
            border: 2px solid #5dade2;
        }
    """
    self.btn_msds_submit.setStyleSheet(button_style)
    submit_button_row = QHBoxLayout()
    submit_button_row.addStretch()
    submit_button_row.addWidget(self.btn_msds_submit)
    submit_button_row.addStretch()  # Center button
    return submit_button_row

def clear_msds_form(self):
    """Clear all input fields and the summary table."""
    global current_msds_id
    try:
        current_msds_id = None  # Reset the global MSDS ID
        # Set Pre-defined text

        # Stop all typing timers (assuming these exist and are QTimer objects)
        if hasattr(self, 'tel_label_timer') and self.tel_label_timer.isActive():
            self.tel_label_timer.stop()
        if hasattr(self, 'facsimile_label_timer') and self.facsimile_label_timer.isActive():
            self.facsimile_label_timer.stop()
        if hasattr(self, 'email_label_timer') and self.email_label_timer.isActive():
            self.email_label_timer.stop()

        self.manufactured_label_input.setPlainText(
            "Masterbatch Philippines, Inc. 24 Diamond Road, Caloocan Industrial Subdivision, Bo. Kaybiga, Caloocan City, Philippines")
        self.tel_label_input.setText("(632) 87088681")
        self.facsimile_label_input.setText("(632) 83747085")
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

            initial_props = [  # Same as in create_dynamic_section9
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
            for name, value in initial_props:
                row = _create_property_row(self, name, value)
                self.physical_properties_layout.insertWidget(self.physical_properties_layout.count() - 1, row)
            _update_property_buttons(self)

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
    """Checks if a QLineEdit or QTextEdit is empty and applies/removes red border."""
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