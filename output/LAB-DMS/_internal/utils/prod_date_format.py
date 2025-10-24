from datetime import datetime

def dates_for_db(date_str):
    """
    Converts one or more dates (dd/mm/yyyy) → yyyy-MM-dd for saving to DB.
    Example:
        "10/09/2025, 10/12/2025, 10/11/2025"
        → "2025-10-09, 2025-10-12, 2025-10-14"
    """
    if not date_str:
        return ""

    formatted = []
    for d in date_str.split(','):
        d = d.strip()
        try:
            parsed = datetime.strptime(d, "%m/%d/%Y")
            formatted.append(parsed.strftime("%Y-%m-%d"))
        except ValueError:
            formatted.append(d)  # Keep as-is if not valid
    return ", ".join(formatted)


def dates_for_display(date_str):
    """
    Converts one or more dates (yyyy-MM-dd) → dd/mm/yyyy for display in input field.
    Example:
        "2025-10-09, 2025-10-12, 2025-10-14"
        → "10/09/2025, 10/12/2025, 10/11/2025"
    """
    if not date_str:
        return ""

    formatted = []
    for d in date_str.split(','):
        d = d.strip()
        try:
            parsed = datetime.strptime(d, "%Y-%m-%d")
            formatted.append(parsed.strftime("%m/%d/%Y"))
        except ValueError:
            formatted.append(d)  # Keep as-is if not valid
    return ", ".join(formatted)