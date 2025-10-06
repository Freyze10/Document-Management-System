import re


def match_customer(self, cx_name):
    from table.coa_data_entry import populate_coa_summary

    if "everest plastic" in cx_name.lower():
        self.coa_others_input.setPlainText("Colorant is free from iron oxide.\n"
                                           "Colorant is suitable from food packaging applications.")

    elif "h&e" in cx_name.lower():
        self.summary_initial_v_header = [
            "Color",
            "Light Fastness (1-8)*",
            "Heat Stability (1-5)**"
        ]
        populate_coa_summary(self)

    elif "global konteiner" in cx_name.lower():
        self.summary_initial_v_header = [
            "Color",
            "Light Fastness (1-8)",
            "Heat Stability (1-5)*"
        ]
        self.coa_others_input.setPlainText("Heat stability testing was done at a "
                                           "temperature of 200-210°C for two minutes. "
                                           "We recommend the users to do their own "
                                           "testing to determine the suitability of "
                                           "the product for their own particular purpose.")
    elif "plastimer" in cx_name.lower():
        self.coa_others_input.setPlainText("RoHS Compliant and Food Contact Approved.")
    elif "zeller" in cx_name.lower():

        self.coa_others_input.setPlainText("ASTM D 1238")

    else:
        self.summary_initial_v_header = [
            "Color",
            "Light Fastness (1-8)",
            "Heat Stability (1-5)"
        ]
        self.coa_others_input.setPlainText("")


def note_summary_table(self, headers, cx_name):
    if "h&e" in cx_name.lower():
        notes = []
        for header in headers:
            header = header.strip()
            stars_match = re.search(r'(\*+)$', header)
            if not stars_match:
                continue
            stars = stars_match.group(1)

            paren_match = re.search(r'\(([^)]*)\)', header)
            paren_content = paren_match.group(1) if paren_match else ""

            header_clean = re.sub(r'\s*\([^)]*\)', '', header)
            header_clean = re.sub(r'\*+$', '', header_clean).strip()

            # Improved number extraction
            low_val, high_val = None, None
            num_match = re.match(r'(\d+)\s*-\s*(\d+)', paren_content)
            if num_match:
                low_val, high_val = num_match.group(1), num_match.group(2)
            else:
                low_val = paren_content[0] if len(paren_content) > 0 else ""
                high_val = paren_content[-1] if len(paren_content) > 0 else ""

            # Special note for migration
            if "migration" in header_clean.lower():
                note = (f"{stars}From a scale of {paren_content} where {high_val} denotes no migration "
                        f"and {low_val} with the highest migration.")
            else:
                note = (f"{stars}From a scale of {paren_content} where {high_val} denotes highest "
                        f"{header_clean.lower()} and {low_val} the lowest {header_clean.lower()}.")
            notes.append(note)

        self.coa_others_input.setPlainText("\n".join(notes))
    # elif "global konteiner" in cx_name.lower():
    #     pass
