
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
    elif "plastimer" in cx_name.lower():
        self.coa_others_input.setPlainText("RoHS Compliant and Food Contact Approved.")

    else:
        self.summary_initial_v_header = [
            "Color",
            "Light Fastness (1-8)",
            "Heat Stability (1-5)"
        ]
        self.coa_others_input.setPlainText("")


def note_summary_table(self, headers, cx_name):
    """
    Appends notes for starred vertical headers: if a header ends with one or more '*',
    adds a note like '*Note text' or '**Note text' to the result list.
    """
    notes = []
    for header in headers:
        header = header.strip()
        # Count stars at the end
        trail = ""
        i = len(header) - 1
        while i >= 0 and header[i] == '*':
            trail += "*"
            i -= 1
        if trail:
            notes.append(f"{trail}Flablablabla")
    print(notes)
