
def match_customer(self, cx_name):
    from table.coa_data_entry import populate_coa_summary

    if "everest plastic" in cx_name.lower():
        self.conditional_customer = 1
        self.coa_others_input.setPlainText("Colorant is free from iron oxide.\n"
                                           "Colorant is suitable from food packaging applications.")
        print("everest")
    elif "h&e" in cx_name.lower():
        self.conditional_customer = 2
        self.summary_initial_v_header = [
            "Color",
            "Light Fastness (1-8)*",
            "Heat Stability (1-5)**"
        ]
    elif "global konteiner" in cx_name.lower():
        self.conditional_customer = 3
        self.summary_initial_v_header = [
            "Color",
            "Light Fastness (1-8)",
            "Heat Stability (1-5)*"
        ]
    else:
        self.conditional_customer = 0
        self.summary_initial_v_header = [
            "Color",
            "Light Fastness (1-8)",
            "Heat Stability (1-5)"
        ]
        self.coa_others_input.setPlainText("")
