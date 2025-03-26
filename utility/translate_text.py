from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import pdfplumber
import docx
import requests
from ratelimit import limits, sleep_and_retry
from dotenv import load_dotenv
import os

app = FastAPI()

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# Rate Limit: 5 requests per minute
REQUEST_LIMIT = 5
TIME_WINDOW = 60  # in seconds

@sleep_and_retry
@limits(calls=REQUEST_LIMIT, period=TIME_WINDOW)
def call_api(prompt):
    """Calls the translation API with the given prompt."""
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048}
    }
    response = requests.post(API_URL, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    elif response.status_code == 429:
        raise HTTPException(status_code=429, detail="API rate limit exceeded. Please wait and try again.")
    else:
        raise HTTPException(status_code=response.status_code, detail=f"API Error: {response.text}")

def extract_text_from_pdf(file):
    """Extracts text from a PDF file."""
    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            return [page.extract_text() or "" for page in pdf.pages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")

def extract_text_from_docx(file):
    """Extracts text from a DOCX file."""
    try:
        file.seek(0)
        doc = docx.Document(file)
        return [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from DOCX: {str(e)}")

def process_text_input(file, text, file_upload):
    """Processes input from a file or text."""
    if file_upload and file:
        if file.filename.endswith(".pdf"):
            extracted_text_list = extract_text_from_pdf(file.file)
        elif file.filename.endswith(".docx"):
            extracted_text_list = extract_text_from_docx(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and DOCX are allowed.")
    elif text:
        extracted_text_list = [text]  
    else:
        raise HTTPException(status_code=400, detail="Either file or text must be provided.")

    extracted_text_list = [t.strip() for t in extracted_text_list if t.strip()]
    if not extracted_text_list:
        raise HTTPException(status_code=400, detail="No text found for translation.")
   
    return extracted_text_list

def translate_text(extracted_text_list, target_language):
    """Translates extracted text."""
    translated_pages = []
    for idx, page_text in enumerate(extracted_text_list, start=1):
        prompt = f"Translate this text to {target_language}:\n\n{page_text}"
        translated_text = call_api(prompt)
        translated_pages.append(f"Page {idx}\n{translated_text}")
   
    return "\n\nPage ".join(translated_pages)