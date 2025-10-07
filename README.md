# PDF OCR Text Extraction Tool

## Overview
This Python script (`main.py`) extracts text from scanned (image-based) PDF documents using Optical Character Recognition (OCR). It converts PDF pages to images with `pdf2image` and processes them with `pytesseract` (powered by Tesseract OCR). The script is designed for documents like the provided DoD reprogramming action PDF ("25-08_IR_Israel_Security_Replacement_Transfer_Fund_Tranche_3.pdf"), which contains budget tables and text that standard PDF libraries can't read directly.

Key features:
- Extracts full text per page with basic cleanup (e.g., normalizing spaces and newlines).
- Detects potential table lines for preview (using simple regex for numeric-heavy rows).
- Saves the full extracted text to `extracted_text.txt`.
- Outputs previews to console for quick review.

**Note**: OCR accuracy is ~90-95% for clean printed documents like this one. Manual review/editing of the output is recommended for precision.

## Prerequisites
- Ubuntu 20.04+ (tested on 22.04 LTS).
- Python 3.8+ (pre-installed on Ubuntu).
- A scanned PDF file (e.g., `25-08_IR_Israel_Security_Replacement_Transfer_Fund_Tranche_3.pdf`).

## Installation
Follow these steps to set up the environment on Ubuntu.

### 1. Update System Packages
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install System Dependencies
Install Tesseract OCR and Poppler (required for PDF-to-image conversion):
```bash
sudo apt install tesseract-ocr poppler-utils -y
```

### 3. Install Python Dependencies
Create a virtual environment (recommended) and install the required Python packages:
```bash
# Install pip and venv if not already (usually pre-installed)
sudo apt install python3-pip python3-venv -y

# Create and activate virtual environment
python3 -m venv ocr_env
source ocr_env/bin/activate

# Install Python packages
pip install pytesseract pdf2image pillow pandas
```

**Note**: If you encounter issues with `pdf2image`, ensure Poppler is in your PATH (it should be after the apt install).

### 4. Download the Script and PDF
- Save the provided `main.py` script to a working directory (e.g., `~/pdf-ocr/`).
- Place your PDF file (`25-08_IR_Israel_Security_Replacement_Transfer_Fund_Tranche_3.pdf`) in the same directory.
- (Optional) Deactivate the virtual env when done: `deactivate`.

## Usage
1. Navigate to the directory containing `main.py` and the PDF:
   ```bash
   cd ~/pdf-ocr/
   source ocr_env/bin/activate  # Activate venv if using one
   ```

2. Run the script:
   ```bash
   python main.py
   ```

3. The script will:
   - Convert the PDF to images (at 300 DPI for accuracy).
   - Run OCR on each page.
   - Print page previews and potential table snippets to the console.
   - Save the full extracted text to `extracted_text.txt`.

### Example Output
```
PDF has 3 pages.

--- Page 1 OCR Text (preview) ---
Unclassified REPROGRAMMING ACTION—Internal REPROGRAMMING Serial Number DoD Serial Number: FY 25-08 IR: Israel Subject: Israel Security Replacement Transfer Fund Tranche 3 ...
==================================================

--- Page 2 OCR Text (preview) ---
NAVY INCREASE +105,252 Weapons Procurement, Navy, 25/27 ...
==================================================

--- Page 3 OCR Text (preview) ---
FY 2025 REPROGRAMMING DECREASE: -657,584 ...
==================================================

Full OCR-extracted text summary:
[Combined cleaned text...]

Potential tables found on 3 pages:
Page 1 table preview:
   0    1     2  ...
...

Full text saved to 'extracted_text.txt'
```

### Customizing the Script
- **Change PDF Path**: Edit `pdf_file` in `main.py` (line near the bottom).
- **Higher Accuracy**: Increase `dpi=300` to `dpi=400` in `convert_from_path()` (slower but sharper).
- **Language**: Add `lang='eng+fra'` in `image_to_string()` for multilingual PDFs.
- **Table Parsing**: The current detection is basic; extend with regex or libraries like `tabula-py` for advanced needs.

## Output Files
- `extracted_text.txt`: Full OCR text with page separators (e.g., `--- Page 1 ---`).
- Console: Page previews and table hints.
- (Optional) Extend the script to save tables as CSV (e.g., uncomment/add `df.to_csv()`).

## Troubleshooting
- **Poppler Error ("Unable to get page count")**: Reinstall Poppler (`sudo apt install --reinstall poppler-utils`) and verify: `pdftoppm -h`.
- **Tesseract Not Found**: Check installation: `tesseract --version`. If missing, reinstall: `sudo apt install tesseract-ocr`.
- **Low OCR Accuracy**: 
  - Ensure the PDF is high-quality (not too low-res).
  - Try higher DPI or preprocess images (e.g., add grayscale conversion in code).
- **Permission Issues**: Run `sudo apt` commands with your user or use `sudo`.
- **Python Errors**: Ensure you're in the virtual env and packages are installed (`pip list`).
- **Large PDFs**: For >10 pages, increase memory or process in batches (modify the loop).

## License
This script is provided as-is for educational/personal use. The extracted content from the sample PDF is unclassified U.S. DoD information (public domain).
