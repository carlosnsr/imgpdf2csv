import os
import sys
import cv2
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
import pandas as pd

# CONFIGURATION: List your exact header names here
TARGET_HEADERS = ["Date", "Description", "Reference", "Amount"]

def extract_structured_data(img_path):
    # Load image
    img = cv2.imread(img_path)
    # Get all text data with coordinates
    d = pytesseract.image_to_data(img, output_type=Output.DICT)

    n_boxes = len(d['level'])
    found_headers = {}
    all_data_points = []

    # 1. Locate Headers and collect all text
    for i in range(n_boxes):
        text = d['text'][i].strip()
        if not text: continue

        # Store all text found for later row-clustering
        all_data_points.append({
            'text': text,
            'x': d['left'][i],
            'y': d['top'][i],
            'w': d['width'][i],
            'h': d['height'][i]
        })

        # Check if this word is one of our headers
        for target in TARGET_HEADERS:
            if target.lower() in text.lower():
                found_headers[target] = d['left'][i]

    if not found_headers:
        return None

    # 2. Sort data into rows based on Y coordinate (with 10px tolerance)
    all_data_points.sort(key=lambda r: r['y'])
    rows = []
    if all_data_points:
        current_row = [all_data_points[0]]
        for p in all_data_points[1:]:
            if abs(p['y'] - current_row[-1]['y']) <= 15: # 15px vertical tolerance
                current_row.append(p)
            else:
                rows.append(current_row)
                current_row = [p]
        rows.append(current_row)

    # 3. Map Row items to Header columns
    final_table = []
    header_x_positions = sorted(found_headers.values())

    for row in rows:
        row_data = {h: "" for h in TARGET_HEADERS}
        row_y = row[0]['y']

        # Skip rows that are above our headers
        if row_y <= min([d['y'] for d in all_data_points if d['text'] in TARGET_HEADERS], default=0):
            continue

        for item in row:
            # Find which header's X-coordinate this item is closest to
            best_header = None
            min_dist = 9999
            for h_name, h_x in found_headers.items():
                dist = abs(item['x'] - h_x)
                if dist < min_dist:
                    min_dist = dist
                    best_header = h_name

            if best_header:
                row_data[best_header] += " " + item['text']

        final_table.append(row_data)

    return pd.DataFrame(final_table)

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract.py <pdf> [start_page]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    start_page = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    print(f"Converting PDF {pdf_path}...")
    pages = convert_from_path(pdf_path, dpi=300, first_page=start_page)

    for i, page in enumerate(pages):
        page_num = i + start_page
        temp_img = f"temp_p{page_num}.png"
        page.save(temp_img, "PNG")

        df = extract_structured_data(temp_img)

        if df is not None and not df.empty:
            out_name = f"extracted_tables/page_{page_num}.csv"
            df.to_csv(out_name, index=False)
            print(f"Page {page_num}: Success! Saved to {out_name}")
        else:
            print(f"Page {page_num}: No matching headers found.")

        os.remove(temp_img)

if __name__ == "__main__":
    os.makedirs("extracted_tables", exist_ok=True)
    main()
