import os
import sys
from pdf2image import convert_from_path
from img2table.document import Image
from img2table.ocr import TesseractOCR
import pandas as pd

def main():
    # 1. Check if a filename was provided
    if len(sys.argv) < 2:
        print("Usage: python extract.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # 2. Check if the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.")
        sys.exit(1)

    output_folder = "extracted_tables"
    os.makedirs(output_folder, exist_ok=True)

    # 3. Convert PDF pages to Images
    print(f"Processing {pdf_path}...")
    try:
        pages = convert_from_path(pdf_path, dpi=300)
    except Exception as e:
        print(f"Failed to convert PDF: {e}")
        sys.exit(1)

    # 4. Initialize OCR Engine
    ocr = TesseractOCR(n_threads=4, lang="eng")

    # 5. Process each page
    for i, page in enumerate(pages):
        img_path = f"temp_page_{i}.jpg"
        page.save(img_path, "JPEG")

        doc = Image(img_path)

        # Extract tables
        tables = doc.extract_tables(ocr=ocr, implicit_rows=True, borderless=True)

        print(f"Page {i+1}: Found {len(tables)} table(s).")

        for idx, table in enumerate(tables):
            df = pd.DataFrame(table.content)
            # Create a clean filename based on the input PDF name
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            csv_name = f"{output_folder}/{base_name}_p{i+1}_t{idx+1}.csv"

            df.to_csv(csv_name, index=False, header=False)
            print(f"  -> Saved: {csv_name}")

        os.remove(img_path)

    print("\nProcessing Complete!")

if __name__ == "__main__":
    main()
