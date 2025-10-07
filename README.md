# PDF OCR to CSV Extraction API

## Overview
This FastAPI-based API (`api.py`) extracts text from scanned (image-based) PDF documents using Optical Character Recognition (OCR). It converts uploaded PDF files to images with `pdf2image` and processes them with `pytesseract` (powered by Tesseract OCR). The extracted text is then sent to an AI inference API (using Anthropic Claude 3 Opus) to parse structured data into a JSON array based on a predefined schema for DoD reprogramming documents. Finally, it generates and returns a downloadable `.csv` file with columns like `appropriation_category`, `reprogramming_amount`, etc.

Key features:
- **POST `/extract-csv`**: Upload a PDF, perform OCR, parse with AI for structured extraction, and download as `.csv`.
- **POST `/extract`**: Legacy endpoint for raw OCR text as `.txt`.
- Handles scanned PDFs like the sample DoD reprogramming action document ("25-08_IR_Israel_Security_Replacement_Transfer_Fund_Tranche_3.pdf"), extracting budget line items (increases/decreases) into rows.
- AI parsing uses a custom system prompt to target specific columns (e.g., fiscal years, budget activities, explanations).
- Basic text cleanup and error handling.
- Interactive docs at `/docs` (Swagger UI).

**Note**: OCR accuracy ~90-95%; AI parsing assumes clean document structure. Output CSV includes one row per reprogramming entry (e.g., Army +$118,600, Navy +$105,252, etc., plus the offset decrease). Review for edge cases.

## Prerequisites
- Ubuntu 20.04+ (tested on 22.04 LTS).
- Python 3.8+ (pre-installed on Ubuntu).
- A scanned PDF file for testing.
- Valid API key for the inference service (hardcoded in code; secure in production via env vars).

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
pip install fastapi uvicorn[standard] pytesseract pdf2image pillow pandas requests
```

**Note**: If you encounter issues with `pdf2image`, ensure Poppler is in your PATH (it should be after the apt install).

### 4. Download the API Code
- Save the provided `api.py` script to a working directory (e.g., `~/pdf-ocr-api/`).
- Update `INFERENCE_API_KEY` in `api.py` with your actual key if needed.
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
   - **Primary: Extract to CSV (Recommended)**:
     Using curl (replace `/path/to/your.pdf` with your file):
     ```bash
     curl -X POST "http://localhost:8000/extract-csv" \
       -H "Content-Type: multipart/form-data" \
       -F "file=@/path/to/25-08_IR_Israel_Security_Replacement_Transfer_Fund_Tranche_3.pdf" \
       --output extracted_data.csv
     ```
     - Downloads `extracted_data.csv` with structured rows (e.g., 6 rows for the sample PDF: 5 increases + 1 decrease).

   - **Legacy: Raw Text Extraction**:
     ```bash
     curl -X POST "http://localhost:8000/extract" \
       -H "Content-Type: multipart/form-data" \
       -F "file=@/path/to/your.pdf" \
       --output extracted_text.txt
     ```

   - **Using Swagger UI** (`/docs`):
     - Click "Try it out" on the `/extract-csv` endpoint.
     - Upload a PDF and execute—the response will be a downloadable `.csv`.

   - **Using Python requests** (example client for CSV):
     ```python
     import requests

     url = "http://localhost:8000/extract-csv"
     with open('your_pdf.pdf', 'rb') as f:
         files = {'file': f}
         response = requests.post(url, files=files)
     if response.status_code == 200:
         with open('extracted.csv', 'wb') as out:
             out.write(response.content)
         print("CSV saved to extracted.csv")
     else:
         print(f"Error: {response.text}")
     ```

### Example Output (CSV for Sample PDF)
The `.csv` will have headers matching the schema and rows like:
```
appropriation_category,appropriation_code,appropriation_activity,branch,fiscal_year_start,fiscal_year_end,budget_activity_number,budget_activity_title,pem,budget_title,program_base_congressional,program_base_dod,reprogramming_amount,revised_program_total,explanation
"Operation and Maintenance, Army, 25/25","25/25","Operating Forces","Army",25,25,"01","Operating Forces",,"Operating Forces",0,0,118600,118600,"Funds are required to reimburse for the deployment of air defense materiel..."
"Weapons Procurement, Navy, 25/27","25/27","Other Missiles – Standard Missile","Navy",25,27,"02","Other Missiles – Standard Missile",,"Standard Missile",0,0,105252,105252,"Funds are required for the replacement of Standard Missiles expended..."
...
"Operation and Maintenance, Defense-Wide, 24/25","24/25","Administration and Servicewide Activities – Israel Security Replacement Transfer Fund","Defense-Wide",24,25,"04","Administration and Servicewide Activities – Israel Security Replacement Transfer Fund",,"Israel Security Replacement Transfer Fund",4400000,3175117,-657584,2517533,"Funds are available from division A of Israel Security Supplemental Appropriations Act..."
```

## API Endpoints
| Method | Endpoint       | Description                          | Parameters                  |
|--------|----------------|--------------------------------------|-----------------------------|
| GET    | `/`            | Health check                        | None                        |
| POST   | `/extract-csv` | OCR + AI parse + CSV download       | `file` (UploadFile): PDF    |
| POST   | `/extract`     | Raw OCR text as .txt (legacy)       | `file` (UploadFile): PDF    |

- **Responses**: Streaming `.csv` or `.txt` file (e.g., `extracted_yourfile.pdf.csv`).
- **Errors**: 400 (invalid file), 500 (OCR/AI failure). Logs details in console.

## Customizing the API
- **AI Prompt/Schema**: Edit `SYSTEM_PROMPT` in `api.py` to adjust columns or instructions.
- **Inference Config**: Change `MODEL`, `MAX_TOKENS`, or `INFERENCE_API_URL`/`KEY`.
- **OCR Tuning**: Adjust `dpi=300` in `convert_from_bytes()` (higher = better accuracy, slower).
- **Language**: Set `lang='eng'` in `image_to_string()` for multilingual support.
- **File Limits**: Add checks in endpoints (e.g., `if len(pdf_bytes) > 10 * 1024**2: raise HTTPException(...)` for 10MB max).
- **Production**: Use `uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4`. Deploy with Docker (see Dockerfile). Secure API key with `os.getenv('INFERENCE_API_KEY')`.

## Docker Support
Build and run with Docker for easy deployment:
1. Create `requirements.txt`:
   ```
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   pytesseract==0.3.10
   pdf2image==1.16.3
   pillow==10.1.0
   pandas==2.1.4
   requests==2.31.0
   ```
2. Use the provided `Dockerfile` to build: `docker build -t pdf-ocr-api .`
3. Run: `docker run -p 8000:8000 -e INFERENCE_API_KEY=your_key pdf-ocr-api`
   - Access at `http://localhost:8000/docs`.

## Output Files
- `.csv`: Structured data with schema columns (one row per budget entry).
- `.txt` (legacy): Raw OCR text with page separators.
- No server-side persistence (in-memory processing).

## Troubleshooting
- **Poppler Error**: Reinstall: `sudo apt install --reinstall poppler-utils`; verify: `pdftoppm -h`.
- **Tesseract Not Found**: Check: `tesseract --version`; reinstall: `sudo apt install tesseract-ocr`.
- **AI API Errors**: Verify key/URL; check rate limits (e.g., 429 status). Test curl example manually.
- **Low Accuracy**: Higher DPI or grayscale preprocessing (`image = image.convert('L')`). For tables, AI handles parsing.
- **Port Conflicts**: Change `port=8000` in `uvicorn.run()`.
- **Permissions**: Ensure file read access; run non-root.
- **Large PDFs**: >50 pages may timeout—add async or batching.
- **JSON Parsing Fails**: AI response must be valid JSON array; tweak prompt if needed.


## License
Provided as-is for educational/personal use. Sample PDF content is unclassified U.S. DoD (public domain).
