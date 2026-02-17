import os
from pdf2image import convert_from_path
from img2table.document import Image
from img2table.ocr import TesseractOCR
import pandas as pd

# CONFIGURATION
PDF_PATH = "your_document.pdf"  # Replace with your file name
OUTPUT_FOLDER = "extracted_tables"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 1. Convert PDF pages to Images (since your data is inside images)
print("Converting PDF pages to images...")
pages = convert_from_path(PDF_PATH, dpi=300)

# 2. Initialize OCR Engine
ocr = TesseractOCR(n_threads=4, lang="eng")

# 3. Process each page
for i, page in enumerate(pages):
    img_path = f"page_{i}.jpg"
    page.save(img_path, "JPEG")

    # Wrap the image for img2table
    doc = Image(img_path)

    # Extract tables - borderless=True helps with form-style layouts
    tables = doc.extract_tables(ocr=ocr, implicit_rows=True, borderless=True)

    print(f"Page {i}: Found {len(tables)} tables.")

    for idx, table in enumerate(tables):
        df = pd.DataFrame(table.content)
        csv_name = f"{OUTPUT_FOLDER}/page_{i}_table_{idx}.csv"
        df.to_csv(csv_name, index=False, header=False)
        print(f" Saved: {csv_name}")

    # Clean up temporary image
    os.remove(img_path)

print("Done! Check the 'extracted_tables' folder.")
