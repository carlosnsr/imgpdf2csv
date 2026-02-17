import sys
import os
import re

def clean_file(filename):
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return

    # Pattern to match: --- Extracting Text: Page [any number] ---
    # \d+ matches one or more digits
    page_header_pattern = re.compile(r"--- Extracting Text: Page \d+ ---")

    cleaned_lines = []

    with open(filename, 'r') as f:
        # Read all lines into a list
        lines = f.readlines()

    # 1. Remove the first line by slicing the list from index 1 onwards
    remaining_lines = lines[1:]

    for line in remaining_lines:
        stripped_line = line.strip()

        # 2. Remove empty lines
        if not stripped_line:
            continue

        # 3. Remove lines matching the Page Header pattern
        if page_header_pattern.search(stripped_line):
            continue

        # If it passes all checks, keep the original line (with its newline)
        cleaned_lines.append(line)

    # Output the result
    output_filename = f"cleaned_{filename}"
    with open(output_filename, 'w') as f:
        f.writelines(cleaned_lines)

    print(f"Success! Cleaned file saved as: {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_text.py <filename>")
    else:
        clean_file(sys.argv[1])
