import sys
import os
import pytesseract
from pdf2image import convert_from_path

def main():
    # 1. Check arguments
    if len(sys.argv) < 3:
        print("Usage: python pdf_to_text.py <pdf_path> <page_number>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        page_num = int(sys.argv[2])
    except ValueError:
        print("Error: Page number must be an integer.")
        sys.exit(1)

    # 2. Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.")
        sys.exit(1)

    print(f"--- Processing Page {page_num} ---")

    # 3. Convert only the specific page to an image
    # We use 300 DPI (standard for OCR)
    try:
        pages = convert_from_path(
            pdf_path,
            dpi=300,
            first_page=page_num,
            last_page=page_num
        )

        if not pages:
            print("Error: Page not found in PDF.")
            sys.exit(1)

        page_image = pages[0]

    except Exception as e:
        print(f"Failed to convert PDF page: {e}")
        sys.exit(1)

    # 4. Perform OCR
    # The 'lang' parameter can be changed if your PDF is not in English
    text = pytesseract.image_to_string(page_image, lang='eng')

    # 5. Output results
    if text.strip():
        print(text)
    else:
        print("No text detected on this page. (It might be blank or very blurry)")

if __name__ == "__main__":
    main()
