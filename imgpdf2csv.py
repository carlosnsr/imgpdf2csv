import os
import sys
import cv2
import numpy as np
from pdf2image import convert_from_path
from img2table.document import Image
from img2table.ocr import TesseractOCR
import pandas as pd

def main():
    # 1. Handle Command Line Arguments
    if len(sys.argv) < 2:
        print("Usage: python extract.py <path_to_pdf> [start_page]")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Check for optional start page (default to 1)
    try:
        start_page = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    except ValueError:
        print("Error: Start page must be a number.")
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.")
        sys.exit(1)

    output_folder = "extracted_tables"
    os.makedirs(output_folder, exist_ok=True)

    # 2. Convert PDF pages to Images
    print(f"Processing {pdf_path} starting from page {start_page}...")
    try:
        # Optimization: We only convert the pages we actually need
        # first_page and last_page are 1-indexed in convert_from_path
        pages = convert_from_path(pdf_path, dpi=600, first_page=start_page)
    except Exception as e:
        print(f"Failed to convert PDF: {e}")
        sys.exit(1)

    # 3. Initialize OCR Engine
    ocr = TesseractOCR(n_threads=4, lang="eng")

    # 4. Process the sliced list of pages
    for i, page in enumerate(pages):
        # Calculate actual page number for labels
        actual_page_num = i + start_page
        img_path = f"temp_page_{actual_page_num}.jpg"
        page.save(img_path, "JPEG")

        # Image Processing
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        processed_img = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        cv2.imwrite(img_path, processed_img)

        doc = Image(img_path)

        # Extraction
        tables = doc.extract_tables(
            ocr=ocr,
            implicit_rows=True,
            borderless_tables=True,
            min_confidence=30
        )

        print(f"Page {actual_page_num}: Found {len(tables)} table(s).")

        for idx, table in enumerate(tables):
            df = pd.DataFrame(table.content)
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            csv_name = f"{output_folder}/{base_name}_p{actual_page_num}_t{idx+1}.csv"

            df.to_csv(csv_name, index=False, header=False)
            print(f"  -> Saved: {csv_name}")

        os.remove(img_path)

    print("\nProcessing Complete!")

if __name__ == "__main__":
    main()
