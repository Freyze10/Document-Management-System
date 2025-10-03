def match_customer(self, cx_name):
    if "everest plastic containers" in cx_name.lower():
        self.coa_others_input.setPlainText("Colorant is free from iron oxide.\n"
                                           "Colorant is suitable from food packaging applications.")

    if "h&e" in cx_name.lower():
        self.summary_initial_v_header = [
            "Color",
            "Light Fastness (1-8)*",
            "Heat Stability (1-5)**"
        ]
    if "global konteiner" in cx_name.lower():
        self.summary_initial_v_header = [
            "Color",
            "Light Fastness (1-8)",
            "Heat Stability (1-5)*"
        ]


