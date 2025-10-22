import re


def normalize(lot_no: str) -> str:
    if not lot_no:
        return ""

    # 1. Initial cleanup: Remove "LOT #" prefixes.
    cleaned_input = re.sub(r"LOT\s*#\s*", "", lot_no, flags=re.IGNORECASE)

    # Split by newlines or semicolons to get primary chunks
    primary_chunks = re.split(r"[\n;]", cleaned_input)

    all_expanded_parts = []
    last_known_prefix_overall = ""

    for chunk in primary_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Split by commas OR multiple spaces (but not inside lot numbers)
        sub_parts = re.split(r",|\s{2,}(?=[A-Z0-9])", chunk)
        last_known_prefix_for_this_chunk = last_known_prefix_overall

        for part in sub_parts:
            part = part.strip()
            if not part:
                continue

            # --- NEW CONDITION: Handle ranges with "TO"
            # Example: MB-20-3321AF TO 3330AF
            to_range_match = re.match(r"^(MB-\d{2}-|\d{2}-)(\d+[A-Z]*)\s+TO\s+(\d+[A-Z]*)$", part, re.IGNORECASE)
            if to_range_match:
                prefix = to_range_match.group(1)
                start_val = to_range_match.group(2)
                end_val = to_range_match.group(3)
                all_expanded_parts.append(f"{prefix}{start_val} TO {prefix}{end_val}")
                last_known_prefix_for_this_chunk = prefix
                last_known_prefix_overall = prefix
                continue

            # --- EXISTING CONDITIONS ---

            # Fully qualified ranges with hyphen (e.g., MB-09-1270I - 1273I)
            fully_qualified_range_match = re.match(r"^(MB-\d{2}-|\d{2}-)(\d+[A-Z]*)\s*-\s*(\d+[A-Z]*)$", part)
            if fully_qualified_range_match:
                prefix = fully_qualified_range_match.group(1)
                start_suffix = fully_qualified_range_match.group(2)
                end_suffix = fully_qualified_range_match.group(3)
                all_expanded_parts.append(f"{prefix}{start_suffix} to {prefix}{end_suffix}")
                last_known_prefix_for_this_chunk = prefix
                last_known_prefix_overall = prefix
                continue

            # Extract prefix from full lot numbers
            current_part_prefix_match = re.match(r"^(MB-\d{2}-|\d{2}-)", part)
            if current_part_prefix_match:
                last_known_prefix_for_this_chunk = current_part_prefix_match.group(1)
                last_known_prefix_overall = current_part_prefix_match.group(1)

            elif re.match(r"^\d+[A-Z]*$", part):
                # suffix only, keep prefix
                pass
            else:
                # unrelated format, reset
                last_known_prefix_for_this_chunk = ""
                last_known_prefix_overall = ""

            # Inline hyphen ranges like MB-25-6351AM-6358AM
            range_match = re.match(r"^(MB-\d{2}-|\d{2}-)(\d+[A-Z]*)-(\d+[A-Z]*)$", part)
            if range_match:
                prefix = range_match.group(1)
                start_val = range_match.group(2)
                end_val = range_match.group(3)
                all_expanded_parts.append(f"{prefix}{start_val} to {prefix}{end_val}")
                last_known_prefix_for_this_chunk = prefix
                last_known_prefix_overall = prefix
                continue

            # Inline suffix-only
            if re.match(r"^\d+[A-Z]*$", part) and last_known_prefix_for_this_chunk:
                all_expanded_parts.append(last_known_prefix_for_this_chunk + part)
                last_known_prefix_overall = last_known_prefix_for_this_chunk
                continue

            # Default: add part as-is
            all_expanded_parts.append(part)

    return ", ".join(all_expanded_parts)


def lot_for_filename(lot_no: str) -> str:
    if not lot_no:
        return ""

    # Split by commas
    parts = [p.strip() for p in lot_no.split(",") if p.strip()]
    result_parts = []

    for part in parts:
        # Handle ranges: "95-5448U to 95-5453U"
        range_match = re.match(r"^(?:MB-\d{2}-|\d{2}-)?(\d+[A-Z]*)\s+to\s+(?:MB-\d{2}-|\d{2}-)?(\d+[A-Z]*)$", part)
        if range_match:
            start = range_match.group(1)
            end = range_match.group(2)
            result_parts.append(f"{start}-{end}")
            continue

        # Handle single lot numbers: "MB-21-4518AG" or "95-2087S"
        single_match = re.match(r"^(?:MB-\d{2}-|\d{2}-)?(\d+[A-Z]*)$", part)
        if single_match:
            result_parts.append(single_match.group(1))
            continue

        # If nothing matches, just keep the original
        result_parts.append(part)

    return ", ".join(result_parts)


def expand_lots(normalized_lots: str) -> str:
    if not normalized_lots:
        return ""

    parts = [p.strip() for p in normalized_lots.split(",") if p.strip()]
    expanded_parts = []

    for part in parts:
        # Check if part is a range: "MB-13-3756N to MB-13-3760N" (case-insensitive 'to')
        range_match = re.match(
            r"^(.*?)(\d+)([A-Za-z]*)\s+to\s+(.*?)(\d+)([A-Za-z]*)$",
            part,
            flags=re.IGNORECASE
        )
        if range_match:
            prefix1, start_num, suffix1, prefix2, end_num, suffix2 = range_match.groups()

            if prefix1 != prefix2 or suffix1 != suffix2:
                # Mismatched range, keep as-is
                expanded_parts.append(part)
                continue

            start_num = int(start_num)
            end_num = int(end_num)

            for i in range(start_num, end_num + 1):
                expanded_parts.append(f"{prefix1}{i}{suffix1}")
        else:
            # Not a range, just append
            expanded_parts.append(part)

    return ", ".join(expanded_parts)