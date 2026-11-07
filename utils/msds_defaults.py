"""
utils/msds_defaults.py  -  default values of the two MSDS sheet types (no Qt in here).

    MB = masterbatch sheet   (MB.docx)  - simplified hazard / storage layout
    DC = DC sheet            (DC.docx)  - detailed hazard + handling/storage layout

Every text below was taken from the two Word documents. What is highlighted
yellow in those documents is what usually changes for every product; it is
listed in USUAL_FIELDS / USUAL_SECTION9 and marked in the entry form.

Keys are the attribute names of the input widgets on the form.
"""
MB = "MB"
DC = "DC"

_COMMON = {
    "manufactured_label_input":
        "Masterbatch Philippines, Inc. 24 Diamond Road, Caloocan Industrial Subdivision, Bo. Kaybiga, Caloocan City, Philippines",
    "tel_label_input": "(632) 70023720",
    "facsimile_label_input": "(63) 9088106546",          # printed as "Mobile/Viber No"
    "email_label_input": "sales@polycolor.biz",
    "stability_reactivity_input": "This product is chemically stable and non-reactive.",
    "conditions_to_avoid_input": "None",
    "materials_to_avoid_input": "None",
    "hazardous_decomposition_input": "None",
    "toxicological_input": "This product is non-toxic and physiologically harmless.",
    "ecological_input": "No known harmful effects to human lives or to the environment.",
    "disposal_input": "If recycling is not practicable, dispose in compliance with local regulation.",
    "regulatory_input":
        "This product is not classified in the list of controlled substances implemented by the government.",
    "msds_shelf_life_input":
        "Twelve months from date of production when the product is stored in unbroken packaging.",
}

_DC = {
    "composition_input": "The preparation consists of organic and inorganic pigments, and other additives.",
    # 3) Hazard - detailed
    "hazard_preliminaries_input": "Inert nuisance dust can cause lung irritation.",
    "hazard_entry_route_input": "Inhalation of airborne dust.",
    "hazard_symptoms_input": "Coughing, sneezing or irritation of the mucous membrane.",
    "hazard_restrictive_condition_input": "Breathing or respiratory tract disorder/disease.",
    "hazard_eyes_input": "Inert foreign body hazard.",
    "hazard_general_note_input":
        "No adverse health effects during the course of normal industrial handling. If large quantities ingested, seek medical attention.",
    "hazard_single_field_input": "",
    # 4) First aid
    "first_aid_inhalation_input": "Remove to fresh air.",
    "first_aid_eyes": "Flush with large amount of water. If irritation persists, seek medical attention.",
    "first_aid_skin_input": "Wash with mild soap.",
    "first_aid_ingestion_input":
        "No adverse health effects during the course of normal industrial handling. If large quantities ingested, seek medical attention.",
    # 5) 6)
    "fire_fighting_media_input":
        "No fire hazard. Precautions should be taken against static discharge of electricity during powder handling operations",
    "accidental_release_input":
        "Use any mechanical means to remove powder. Avoid dusting. Prevent entry to natural waterways.",
    # 7) Handling and Storage - detailed
    "handling_input":
        "Use suitable ventilation to prevent excessive inhalation and skin contact. Avoid static discharge during powder handling operation.",
    "msds_storage_input":
        "Store in dry area, wet material may become very slippery. Close bag after use to prevent moisture intake & soiling.",
    "msds_storage_single_input": "",
    # 8) Exposure controls
    "exposure_control_input":
        "Generally handle in areas of good ventilation. If airborne dust is over or thought to approach the occupational exposure standard, local exhaust may be necessary.",
    "respiratory_protection_input":
        "Use approved dust respirator if occupational exposure standard is likely to be exceeded.",
    "hand_protection_input": "Use gloves for prolonged/repeated contact.",
    "eye_protection_input": "Use safety glasses/ goggles.",
    "skin_protection_input":
        "Wear normal protective overalls. Sensitive skin can be protected further by use of barrier cream or moisturizer.",
    "transport_input":
        "This material is not classified as a dangerous good by International Transport regulation.",
    "other_input": "None",
}

_MB = {
    "composition_input": "The preparation consists of organic pigments, polyolefin resin and other additives.",
    # 3) Hazard - simplified (the detailed boxes stay empty)
    "hazard_preliminaries_input": "",
    "hazard_entry_route_input": "",
    "hazard_symptoms_input": "",
    "hazard_restrictive_condition_input": "",
    "hazard_eyes_input": "",
    "hazard_general_note_input": "",
    "hazard_single_field_input": "No known harmful effects to human lives or to the environment.",
    # 4) First aid
    "first_aid_inhalation_input": "N/A",
    "first_aid_eyes": "N/A",
    "first_aid_skin_input": "N/A",
    "first_aid_ingestion_input": "N/A",
    # 5) 6)
    "fire_fighting_media_input": "Water spray, dry powder, foam, carbon dioxide",
    "accidental_release_input": "Use any mechanical means to remove pellet. Prevent entry to natural waterways.",
    # 7) Handling / Storage - simplified (storage only)
    "handling_input": "",
    "msds_storage_input": "",
    "msds_storage_single_input":
        "Store in a dry place and shaded area. Close bag after use to prevent moisture intake & soiling.",
    # 8) Exposure controls
    "exposure_control_input":
        "Generally, handle in accordance with good industrial hygiene and safety practices.",
    "respiratory_protection_input": "None",
    "hand_protection_input": "None",
    "eye_protection_input": "None",
    "skin_protection_input": "None",
    "transport_input":
        "This material is not classified as a dangerous good by the International Transport regulation.",
    "other_input": "",          # e.g. "PICASSO Number 5080955" - different for every product
}

DEFAULTS = {DC: {**_COMMON, **_DC}, MB: {**_COMMON, **_MB}}

# 9) Physical & Chemical Properties
SECTION9 = {
    DC: [
        ("Appearance", "White powder form"),
        ("Odor", "Odorless"),
        ("Heat Stability (1-5)", ""),
        ("Light fastness (1-8)", ""),
        ("Decomposition", "N/A"),
        ("Flash Point", "N/A"),
        ("Auto Ignition", "N/A"),
        ("Explosion Property", "N/A"),
        ("Solubility (Water)", "Insoluble"),
    ],
    MB: [
        ("Appearance", "White pellet form"),
        ("Odor", "Odorless"),
        ("Packaging", "25 kgs."),
        ("Carrier Material", "Polyolefin resin"),
        ("Resin Suitability", "Polyolefin"),
        ("Light fastness (1-8)", ""),
        ("Heat Stability (1-5)", ""),
        ("Flash Point", "N/A"),
        ("Auto Ignition", "N/A"),
        ("Explosion Property", "N/A"),
        ("Solubility (Water)", "Insoluble"),
    ],
}

# --- what is highlighted yellow in the Word documents = usually changed per product ---
USUAL_FIELDS = ("trade_label_input", "composition_input", "other_input")
USUAL_SECTION9 = {
    DC: {"appearance", "heat stability (1-5)", "light fastness (1-8)"},
    MB: {"appearance", "carrier material", "resin suitability", "light fastness (1-8)", "heat stability (1-5)"},
}

PLACEHOLDERS = {
    "trade_label_input": {DC: "e.g. Colorant Pink DP-K14150E", MB: "e.g. Masterbatch Red RA6804E"},
    "other_input": {DC: "", MB: "e.g. PICASSO Number 5080955"},
}

# Hidden-page fields: always rewritten when the sheet type is switched, so a MB sheet
# never keeps DC hazard text (the print picks the template from these fields).
FORCE_ON_SWITCH = (
    "hazard_preliminaries_input", "hazard_entry_route_input", "hazard_symptoms_input",
    "hazard_restrictive_condition_input", "hazard_eyes_input", "hazard_general_note_input",
    "hazard_single_field_input", "handling_input", "msds_storage_input", "msds_storage_single_input",
)


# --------------------------------------------------------------------------
# logic (pure functions, easy to test)
# --------------------------------------------------------------------------
def defaults(mode):
    return DEFAULTS[mode]


def section9_defaults(mode):
    return list(SECTION9[mode])


def is_usual_section9(mode, name):
    return (name or "").strip().lower() in USUAL_SECTION9[mode]


def switch_values(current, old_mode, new_mode):
    """Which fields get a new text when the sheet type changes?

    current  {attr: text now in the box}
    -> {attr: new text}

    A box that still holds the OLD type's default is switched to the new default.
    A box the user has typed in is left alone, except the layout fields in FORCE_ON_SWITCH."""
    old, new = DEFAULTS[old_mode], DEFAULTS[new_mode]
    out = {}
    for attr, text in new.items():
        if attr in FORCE_ON_SWITCH:
            out[attr] = text
        elif attr in current and current[attr].strip() == old.get(attr, "").strip():
            out[attr] = text
    return out


def merge_section9(current_rows, old_mode, new_mode):
    """Section 9 after a switch.

    current_rows [(name, value), ...] as typed now
    - every row of the new type is listed, in the new order
    - a value the user typed is kept, an untouched old default becomes the new default
    - rows the user added or edited that the new type does not have are kept at the end
    - untouched old-type-only rows (e.g. 'Decomposition: N/A') are dropped"""
    old_default = {n.lower(): v for n, v in SECTION9[old_mode]}
    cur = {}
    for name, value in current_rows:
        cur.setdefault(name.strip().lower(), (name, value))

    out, used = [], set()
    for name, default_value in SECTION9[new_mode]:
        key = name.lower()
        used.add(key)
        if key in cur:
            value = cur[key][1]
            untouched = key in old_default and value.strip() == old_default[key].strip()
            out.append((name, default_value if untouched else value))
        else:
            out.append((name, default_value))

    for name, value in current_rows:
        key = name.strip().lower()
        if key in used:
            continue
        untouched = key in old_default and value.strip() == old_default[key].strip()
        if not untouched:
            out.append((name, value))
    return out