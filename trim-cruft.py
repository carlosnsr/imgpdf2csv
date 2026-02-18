import sys
import os
import re

def clean_file(filename):
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return

    # Pattern for page headers: --- Extracting Text: Page [number] ---
    page_header_pattern = re.compile(r"--- Extracting Text: Page \d+ ---")

    cleaned_lines = []

    # This flag tracks if we are currently inside the "Farmer's Insurance" junk block
    in_skipped_block = False

    with open(filename, 'r') as f:
        lines = f.readlines()

    if not lines:
        print("File is empty.")
        return

    # 1. Remove the first line (index 0)
    remaining_lines = lines[1:]

    for line in remaining_lines:
        stripped_line = line.strip()

        # 2. Block Removal Logic (Farmers Insurance -> Import Template)
        # Check if we hit the start of the junk block
        if stripped_line.startswith("Soa Farmers Insurance Exchange"):
            in_skipped_block = True
            continue # Skip this line

        # Check if we hit the end of the junk block
        if in_skipped_block:
            if "myclaim@farmersinsurance.com" in stripped_line:
                in_skipped_block = False
            continue # Skip every line while the flag is True

        # 3. Standard Cleaning
        # Remove empty lines
        if not stripped_line:
            continue

        # Remove Page Headers
        if page_header_pattern.search(stripped_line):
            continue

        if "XactContents Import Template" in stripped_line:
            continue

        if "COLIN_SHUKIE11" in stripped_line:
            continue

        if "COLIN SHUKIE11" in stripped_line:
            continue

        if stripped_line.upper().startswith("CONTINUED - "):
            line = line[12:]

        if stripped_line.startswith("Page: "):
            continue

        if re.match(r"^\d+/\d+/\d+$", stripped_line):
            continue

        if re.match(r"^\d+/\d+/\d+ Page:", stripped_line):
            continue

        # If we made it here, the line is "clean"
        cleaned_lines.append(line)

    # Save the output
    output_filename = f"cleaned_{filename}"
    with open(output_filename, 'w') as f:
        f.writelines(cleaned_lines)

    print(f"Success! Processed {len(lines)} lines down to {len(cleaned_lines)}.")
    print(f"Cleaned file saved as: {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_text.py <filename>")
    else:
        clean_file(sys.argv[1])
