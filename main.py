import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
import re
from io import StringIO


def ocr_pdf(pdf_path):
    full_text = ""
    pages_data = []

    try:
        # Convert PDF pages to images
        images = convert_from_path(
            pdf_path, dpi=300
        )  # Higher DPI for better OCR accuracy
        print(f"PDF has {len(images)} pages.")

        for page_num, image in enumerate(images, start=1):
            # Perform OCR on the image
            page_text = pytesseract.image_to_string(image, lang="eng")

            # Basic cleanup: Remove extra newlines, normalize spaces
            page_text = re.sub(
                r"\n\s*\n", "\n\n", page_text
            )  # Collapse multiple newlines
            page_text = re.sub(r"\s+", " ", page_text)  # Normalize spaces
            page_text = page_text.strip()

            full_text += f"\n--- Page {page_num} ---\n{page_text}\n"
            print(f"\n--- Page {page_num} OCR Text (preview) ---\n{page_text[:500]}...")

            # Simple table detection: Look for lines with tab-like separators or numbers
            # (This is basic; for complex tables, post-process with regex or manual parsing)
            table_lines = [
                line
                for line in page_text.split("\n")
                if re.search(r"\d+[,\d]*", line) and len(line.split()) > 5
            ]
            if table_lines:
                # Mock table as DataFrame (improve with better parsing if needed)
                df = pd.read_csv(
                    StringIO("\n".join(table_lines)), sep="\s+", header=None
                )
                pages_data.append(
                    {
                        "page": page_num,
                        "table_preview": df.head().to_string(index=False),
                    }
                )
                print(
                    f"Potential table lines on Page {page_num}:\n{chr(10).join(table_lines[:3])}...\n"
                )

            print("\n" + "=" * 50 + "\n")

        return full_text, pages_data

    except FileNotFoundError:
        print(f"Error: PDF file '{pdf_path}' not found.")
        return "", []
    except Exception as e:
        print(f"Error during OCR: {e}")
        return "", []


if __name__ == "__main__":
    pdf_file = "25-08_IR_Israel_Security_Replacement_Transfer_Fund_Tranche_3.pdf"
    text_content, page_tables = ocr_pdf(pdf_file)

    print("\nFull OCR-extracted text summary:")
    print(text_content[:1500] + "..." if len(text_content) > 1500 else text_content)

    print(f"\nPotential tables found on {len(page_tables)} pages:")
    for item in page_tables:
        print(f"\nPage {item['page']} table preview:\n{item['table_preview']}")

    # Save full text to file
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text_content)
    print("\nFull text saved to 'extracted_text.txt'")
