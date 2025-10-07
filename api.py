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

app = FastAPI(
    title="PDF OCR Extraction API",
    description="API to extract text from scanned PDFs using OCR and return as .txt file",
)


def ocr_pdf_from_bytes(pdf_bytes: bytes):
    """
    Extract text from PDF bytes using OCR.
    Returns the full cleaned text.
    """
    full_text = ""

    try:
        # Convert PDF bytes to images
        images = convert_from_bytes(
            pdf_bytes, dpi=300
        )  # Higher DPI for better accuracy

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

        return full_text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")


@app.post("/extract", summary="Extract text from uploaded PDF")
async def extract_text(
    file: UploadFile = File(..., description="Scanned PDF file to process")
):
    """
    Upload a PDF file, perform OCR extraction, and download the result as .txt.

    - **file**: The PDF file (multipart/form-data).
    - Returns: StreamingResponse with .txt content.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read PDF bytes
    pdf_bytes = await file.read()

    # Extract text
    extracted_text = ocr_pdf_from_bytes(pdf_bytes)

    if not extracted_text.strip():
        raise HTTPException(
            status_code=500, detail="No text could be extracted from the PDF"
        )

    # Create in-memory .txt file
    txt_io = io.StringIO(extracted_text)

    # Return as downloadable file
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
        "message": "PDF OCR Extraction API is running. Use POST /extract to upload a PDF."
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
