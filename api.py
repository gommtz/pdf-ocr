from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import io
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
import pandas as pd
from io import StringIO
import tempfile
import os
import requests
import json
from typing import List, Dict

# Initialize FastAPI app
app = FastAPI(
    title="PDF OCR to CSV Extraction API",
    description="API to extract text from scanned PDFs using OCR, parse structured data with AI, and return as CSV",
)

# Configuration for the AI inference API
INFERENCE_API_URL = "https://inference.do-ai.run/v1/chat/completions"
INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY")
MODEL = "anthropic-claude-3-opus"
MAX_TOKENS = 2600

# System prompt for extraction
SYSTEM_PROMPT = """You are a helpful assistant specialized in extracting structured data from DoD reprogramming action documents.

Extract the following columns from the PDF document for each reprogramming entry (increases and decreases). Output ONLY a valid JSON array of objects, one per row, with these exact keys (use null or empty string if data is missing/unavailable):

- appropriation_category: e.g., "Operation and Maintenance, Army"
- appropriation_code: e.g., "25/25"
- appropriation_activity: e.g., full activity description
- branch: e.g., "Army", "Navy", "Air Force", "Defense-Wide"
- fiscal_year_start: e.g., 25 (as integer)
- fiscal_year_end: e.g., 25 (as integer)
- budget_activity_number: e.g., "01" (as string)
- budget_activity_title: e.g., "Operating Forces"
- pem: Program Element Measure code if present, else null
- budget_title: e.g., "Operating Forces"
- program_base_congressional: Base amount reflecting congressional action (thousands of dollars, as integer)
- program_base_dod: Program previously approved by Sec Def (thousands of dollars, as integer)
- reprogramming_amount: The reprogramming change (e.g., +118600 or -657584, as integer)
- revised_program_total: Revised program after change (thousands of dollars, as integer)
- explanation: Full explanation text for this entry

Parse all entries from the document, including totals if applicable, but focus on line items. Ensure numbers are without commas or $ signs."""


def ocr_pdf_from_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using OCR.
    Returns the full cleaned text.
    """
    full_text = ""

    try:
        # Convert PDF bytes to images
        images = convert_from_bytes(pdf_bytes, dpi=300)

        for page_num, image in enumerate(images, start=1):
            # Perform OCR on the image
            page_text = pytesseract.image_to_string(image, lang="eng")

            # Basic cleanup
            page_text = re.sub(r"\n\s*\n", "\n\n", page_text)
            page_text = re.sub(r"\s+", " ", page_text)
            page_text = page_text.strip()

            full_text += f"\n--- Page {page_num} ---\n{page_text}\n"

        return full_text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")


def parse_text_with_ai(extracted_text: str) -> List[Dict]:
    """
    Send extracted text to AI inference API to parse into structured JSON.
    Returns list of dicts for CSV rows.
    """
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": extracted_text},
        ],
        "stream": False,
        "max_tokens": MAX_TOKENS,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {INFERENCE_API_KEY}",
    }

    try:
        response = requests.post(INFERENCE_API_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON from content (assume it's wrapped in ```json ... ``` or direct)
        json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content

        data = json.loads(json_str)
        if isinstance(data, list):
            return data
        else:
            raise ValueError("AI response is not a JSON array")

    except requests.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"AI parsing API call failed: {str(e)}"
        )
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to parse AI response: {str(e)}"
        )


def generate_csv_from_data(data: List[Dict]) -> str:
    """
    Generate CSV string from list of dicts.
    """
    if not data:
        raise HTTPException(status_code=500, detail="No data extracted for CSV")

    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()


@app.post("/extract-csv", summary="Extract structured data from PDF and return CSV")
async def extract_to_csv(
    file: UploadFile = File(..., description="Scanned PDF file to process")
):
    """
    Upload a PDF, perform OCR, parse with AI, and download structured data as CSV.

    - **file**: The PDF file (multipart/form-data).
    - Returns: StreamingResponse with .csv content.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read PDF bytes
    pdf_bytes = await file.read()

    # Extract text via OCR
    extracted_text = ocr_pdf_from_bytes(pdf_bytes)

    if not extracted_text.strip():
        raise HTTPException(
            status_code=500, detail="No text could be extracted from the PDF"
        )

    # Parse with AI
    structured_data = parse_text_with_ai(extracted_text)

    # Generate CSV
    csv_content = generate_csv_from_data(structured_data)

    # Create in-memory CSV file
    csv_io = io.StringIO(csv_content)

    # Return as downloadable file
    return StreamingResponse(
        csv_io,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=extracted_{file.filename[:-4]}.csv"
        },
    )


# Keep the original /extract for .txt if needed
@app.post("/extract", summary="Extract raw text from uploaded PDF")
async def extract_text(
    file: UploadFile = File(..., description="Scanned PDF file to process")
):
    """
    Upload a PDF file and download raw OCR text as .txt (legacy endpoint).
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()
    extracted_text = ocr_pdf_from_bytes(pdf_bytes)

    if not extracted_text.strip():
        raise HTTPException(
            status_code=500, detail="No text could be extracted from the PDF"
        )

    txt_io = io.StringIO(extracted_text)
    return StreamingResponse(
        txt_io,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=extracted_{file.filename}.txt"
        },
    )


@app.get("/")
async def root():
    return {
        "message": "PDF OCR to CSV Extraction API is running. Use POST /extract-csv for structured CSV output."
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
