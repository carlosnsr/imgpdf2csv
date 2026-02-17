import os
import sys
import cv2
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
import pandas as pd

# CONFIGURATION: Adjust these based on your specific form layout
# These define the horizontal 'lanes' (in pixels) for your columns
# You may need to tweak these numbers after seeing the first run
COLUMNS = {
    "Description": (0, 1200),  # From left edge to 1200px
    "Quantity": (1201, 1500), # The lane where Quantity usually sits
    "Unit": (1501, 1800),     # The lane where Unit sits
    "Price": (1801, 2500)     # The lane where Price sits
}

def process_page(img_path):
    img = cv2.imread(img_path)
    # Get high-resolution data from Tesseract
    d = pytesseract.image_to_data(img, output_type=Output.DICT)

    # 1. Group words into horizontal lines
    raw_lines = {}
    for i in range(len(d['text'])):
        text = d['text'][i].strip()
        if not text: continue

        y = d['top'][i]
        x = d['left'][i]

        # Merge words that are within 15 pixels vertically into the same line
        found_line = False
        for line_y in raw_lines.keys():
            if abs(y - line_y) < 15:
                raw_lines[line_y].append({'text': text, 'x': x})
                found_line = True
                break
        if not found_line:
            raw_lines[y] = [{'text': text, 'x': x}]

    # 2. Sort lines from top to bottom
    sorted_y = sorted(raw_lines.keys())

    final_data = []
    current_entry = None

    for y in sorted_y:
        line_content = raw_lines[y]
        # Sort words in line from left to right
        line_content.sort(key=lambda w: w['x'])

        # Categorize text into our 'Lanes'
        row_cells = {col: "" for col in COLUMNS}
        has_qty_data = False

        for word in line_content:
            for col_name, (x_min, x_max) in COLUMNS.items():
                if x_min <= word['x'] <= x_max:
                    row_cells[col_name] += word['text'] + " "
                    # Check if this row is a "Main Line" (has data in Qty, Unit, or Price)
                    if col_name != "Description" and word['text'].strip():
                        has_qty_data = True

        row_cells = {k: v.strip() for k, v in row_cells.items()}

        # 3. Wrapping Logic
        # If the row has Qty/Price data OR starts with a clear number/code, it's a NEW row
        if has_qty_data:
            if current_entry:
                final_data.append(current_entry)
            current_entry = row_cells
        else:
            # If it's just text in the Description lane, append to the previous row
            if current_entry:
                current_entry["Description"] += " " + row_cells["Description"]
            else:
                # In case the first row found is just text
                current_entry = row_cells

    if current_entry:
        final_data.append(current_entry)

    return pd.DataFrame(final_data)

def main():
    if len(sys.argv) < 3:
        print("Usage: python form_extractor.py <pdf_path> <page_number>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2])

    print(f"Extracting Page {page_num} from {pdf_path}...")

    # Extract only the specific page requested
    pages = convert_from_path(pdf_path, dpi=300, first_page=page_num, last_page=page_num)

    if not pages:
        print("Page not found.")
        return

    temp_img = "debug_page.png"
    pages[0].save(temp_img, "PNG")

    df = process_page(temp_img)

    # Cleanup and Save
    output_name = f"extracted_page_{page_num}.csv"
    df.to_csv(output_name, index=False)
    os.remove(temp_img)
    print(f"Success! Created {output_name}")

if __name__ == "__main__":
    main()
