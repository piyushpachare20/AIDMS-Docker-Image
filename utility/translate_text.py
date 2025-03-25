from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import pdfplumber
import docx
import requests
from ratelimit import limits, sleep_and_retry
from dotenv import load_dotenv
import os

router = APIRouter()

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# Rate Limit: 5 requests per minute
REQUEST_LIMIT = 5
TIME_WINDOW = 60  # in seconds

@sleep_and_retry
@limits(calls=REQUEST_LIMIT, period=TIME_WINDOW)
def call_api(data):
    headers = {"Content-Type": "application/json"}
    response = requests.post(API_URL, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    elif response.status_code == 429:  # Too Many Requests
        raise HTTPException(status_code=429, detail="API rate limit exceeded. Please wait and try again.")
    else:
        raise HTTPException(status_code=response.status_code, detail=f"API Error: {response.text}")

def extract_text_from_pdf(file):
    """Extracts text from a PDF file."""
    try:
        file.seek(0)  # Reset file pointer before reading
        with pdfplumber.open(file) as pdf:
            return [page.extract_text() or "" for page in pdf.pages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")

def extract_text_from_docx(file):
    """Extracts text from a DOCX file."""
    try:
        file.seek(0)  # Reset file pointer before reading
        doc = docx.Document(file)
        return [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from DOCX: {str(e)}")

@router.post("/translate/")
async def translate_endpoint(
    file: UploadFile = File(None),
    text: str = Form(None),
    target_language: str = Form(...),
    file_upload: bool = Form(...)
):
    try:
        translated_pages = []

        # Extract text from file if provided
        if file_upload and file:
            if file.filename.endswith(".pdf"):
                extracted_text_list = extract_text_from_pdf(file.file)
            elif file.filename.endswith(".docx"):
                extracted_text_list = extract_text_from_docx(file.file)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and DOCX are allowed.")
        elif text:
            extracted_text_list = [text]  # Treat input text as a single page
        else:
            raise HTTPException(status_code=400, detail="Either file or text must be provided")

        # Ensure text is not empty
        extracted_text_list = [t.strip() for t in extracted_text_list if t.strip()]
        if not extracted_text_list:
            raise HTTPException(status_code=400, detail="No text found for translation")

        # Translate each page separately
        for idx, page_text in enumerate(extracted_text_list, start=1):
            prompt = f"Translate this text to {target_language}:\n\n{page_text}"
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 2048
                }
            }
            translated_text = call_api(data)
            translated_pages.append(f"Page {idx}\n{translated_text}")

        # Join all translated pages with page separators
        final_translation = "\n\nPage ".join(translated_pages)
        return {"translated_text": final_translation}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))