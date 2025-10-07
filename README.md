# PDF OCR Extraction API

## Overview
This FastAPI-based API (`api.py`) extracts text from scanned (image-based) PDF documents using Optical Character Recognition (OCR). It converts uploaded PDF files to images with `pdf2image` and processes them with `pytesseract` (powered by Tesseract OCR). The API endpoint accepts a PDF upload and returns the extracted text as a downloadable `.txt` file.

Key features:
- POST `/extract`: Upload a PDF and receive OCR-extracted text as a `.txt` attachment.
- Handles scanned PDFs like the sample DoD reprogramming document ("25-08_IR_Israel_Security_Replacement_Transfer_Fund_Tranche_3.pdf"), which includes budget tables and structured text.
- Basic text cleanup (e.g., normalizing spaces and newlines).
- Error handling for invalid files or extraction failures.
- Interactive docs at `/docs` (Swagger UI).

**Note**: OCR accuracy is ~90-95% for clean printed documents. The output includes page separators (e.g., `--- Page 1 ---`). For table-heavy PDFs, review the `.txt` and parse further if needed.

## Prerequisites
- Ubuntu 20.04+ (tested on 22.04 LTS).
- Python 3.8+ (pre-installed on Ubuntu).
- A scanned PDF file for testing.

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
python3 -m venv ocr_api_env
source ocr_api_env/bin/activate

# Install Python packages
pip install fastapi uvicorn[standard] pytesseract pdf2image pillow pandas
```

**Note**: If you encounter issues with `pdf2image`, ensure Poppler is in your PATH (it should be after the apt install).

### 4. Download the API Code
- Save the provided `api.py` script to a working directory (e.g., `~/pdf-ocr-api/`).
- (Optional) Deactivate the virtual env when done: `deactivate`.

## Usage
1. Navigate to the directory containing `api.py`:
   ```bash
   cd ~/pdf-ocr-api/
   source ocr_api_env/bin/activate  # Activate venv if using one
   ```

2. Run the API server:
   ```bash
   python api.py
   ```
   - The server starts at `http://localhost:8000` (or `http://0.0.0.0:8000` for network access).
   - Open `http://localhost:8000/docs` in your browser for interactive API documentation and testing.

3. **Test the API**:
   - **Using curl** (replace `/path/to/your.pdf` with your file):
     ```bash
     curl -X POST "http://localhost:8000/extract" \
       -H "accept: application/json" \
       -H "Content-Type: multipart/form-data" \
       -F "file=@/path/to/25-08_IR_Israel_Security_Replacement_Transfer_Fund_Tranche_3.pdf" \
       --output extracted_text.txt
     ```
     - This downloads `extracted_text.txt` with the OCR output.

   - **Using Swagger UI** (`/docs`):
     - Click "Try it out" on the `/extract` endpoint.
     - Upload a PDF file and execute—the response will be a downloadable `.txt`.

   - **Using Python requests** (example client script):
     ```python
     import requests

     url = "http://localhost:8000/extract"
     files = {'file': open('your_pdf.pdf', 'rb')}
     response = requests.post(url, files=files)
     if response.status_code == 200:
         with open('extracted.txt', 'wb') as f:
             f.write(response.content)
         print("Extraction saved to extracted.txt")
     else:
         print(f"Error: {response.text}")
     ```

### Example Output
For the sample PDF, the `.txt` file will contain something like:
```
--- Page 1 ---
Unclassified REPROGRAMMING ACTION—Internal REPROGRAMMING Serial Number DoD Serial Number: FY 25-08 IR: Israel Subject: Israel Security Replacement Transfer Fund Tranche 3 Appropriation Title: Various Appropriations Includes Transfer? Yes

Component Serial Number: Program Base Reflecting Program Previously Approved by Sec Def Reprogramming Action Revised Program
(Amounts in Thousands of Dollars)
Line Pub Law b Congressional Action d e f g h i

This reprogramming action provides funding for the replacement of defense articles from the stocks of the Department of Defense expended in support of Israel or identified and notified to Congress for provision to Israel. The administrative and legal requirements, in none of the interests. This reprogramming action has been determined by all Congress.

[... continued for Army increase +118,600 ...]

--- Page 2 ---
[... Navy +105,252, Air Force +77,482 (Sidewinder +14,500, AMRAAM +62,982), Defense-Wide +356,250 ...]

--- Page 3 ---
[... Decrease -657,584 from Defense-Wide ...]
```

## API Endpoints
| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET    | `/`      | Health check | None |
| POST   | `/extract` | Upload PDF and get extracted `.txt` | `file` (UploadFile): Scanned PDF |

- **Response**: Streaming `.txt` file (e.g., `extracted_yourfile.pdf.txt`).
- **Errors**: 400 (invalid file), 500 (extraction failure).

## Customizing the API
- **DPI/Accuracy**: Edit `dpi=300` in `convert_from_bytes()` in `api.py` (higher = better but slower).
- **Language**: Change `lang='eng'` in `image_to_string()` for other languages.
- **Add Table Extraction**: Extend `ocr_pdf_from_bytes` to parse tables (e.g., return JSON with DataFrames).
- **File Limits**: Add size checks in `/extract` (e.g., `if len(pdf_bytes) > 10 * 1024 * 1024: raise HTTPException(...)` for 10MB max).
- **Production**: Use `uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4` for multi-worker mode. Deploy with Docker/NGINX for scalability.

## Output Files
- Downloaded `.txt`: Full OCR text with page separators.
- No server-side files saved (in-memory processing).

## Troubleshooting
- **Poppler Error ("Unable to get page count")**: Reinstall Poppler (`sudo apt install --reinstall poppler-utils`) and verify: `pdftoppm -h`.
- **Tesseract Not Found**: Check: `tesseract --version`. Reinstall if needed: `sudo apt install tesseract-ocr`.
- **Low OCR Accuracy**: Use higher DPI or ensure PDF quality. Preprocess images (e.g., add `image.convert('L')` for grayscale).
- **Port in Use**: Change `port=8000` in `uvicorn.run()`.
- **Permission Issues**: Ensure read access to uploaded files; run as non-root.
- **Python Errors**: Verify virtual env activation and packages (`pip list`). Restart server after changes.
- **Large PDFs**: For >50 pages, timeout may occur—increase `uvicorn` timeout or process asynchronously.


## License
This API is provided as-is for educational/personal use. Extracted content from sample PDFs is unclassified U.S. DoD information (public domain).
