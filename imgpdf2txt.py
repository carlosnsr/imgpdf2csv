import sys
import os
import pytesseract
from pdf2image import convert_from_path

def conv_num(maybe, msg):
    try:
        num = int(maybe)
    except ValueError:
        print(f"Error: {msg} must be a number.")
        sys.exit(1)

    return num

def main():
    # 1. Check arguments
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_text.py <pdf_path>")
        print("Usage: python pdf_to_text.py <pdf_path> <start_page>")
        print("Usage: python pdf_to_text.py <pdf_path> <start_page> <end_page>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    start_page = conv_num(sys.argv[2], "Start page") if len(sys.argv) > 2 else 1
    end_page = conv_num(sys.argv[3], "End page") if len(sys.argv) > 3 else None

    # 2. Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.")
        sys.exit(1)

    # 3. Convert the specified pages to an images
    try:
        print(f"Reading {pdf_path} (Pages {start_page} to {end_page if end_page else 'End'})...")

        pages = convert_from_path(
            pdf_path,
            dpi=300,
            first_page=start_page,
            last_page=end_page
        )

        if not pages:
            print("Error: Pages not found in PDF.")
            sys.exit(1)

    except Exception as e:
        print(f"Failed to convert PDF page: {e}")
        sys.exit(1)

    for i, page_image in enumerate(pages, start=start_page):
        print(f"\n--- Extracting Text: Page {i} ---")

        text = pytesseract.image_to_string(page_image, lang='eng')

        if text.strip():
            print(text)
        else:
            print("No text detected on this page. (It might be blank or very blurry)")

if __name__ == "__main__":
    main()
