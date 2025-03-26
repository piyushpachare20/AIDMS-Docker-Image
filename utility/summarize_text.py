import os
import requests
import pdfplumber
import docx
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

app = FastAPI()

def extract_text(file: UploadFile) -> str:
    """Extracts text from a PDF or DOCX file."""
    if file.filename.endswith(".pdf"):
        return extract_text_from_pdf(file.file)
    elif file.filename.endswith(".docx"):
        return extract_text_from_docx(file.file)
    return ""

def extract_text_from_pdf(uploaded_file) -> str:
    """Extracts text from a PDF file."""
    with pdfplumber.open(uploaded_file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def extract_text_from_docx(uploaded_file) -> str:
    """Extracts text from a DOCX file."""
    doc = docx.Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs])

def summarize_text(text: str) -> str:
    """Calls the API to summarize the extracted text."""
    if not text.strip():
        return "No text found to summarize."
   
    data = {
        "contents": [{
            "parts": [{"text": f"Summarize this:\n{text}"}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024
        }
    }
   
    response = requests.post(API_URL, json=data)
    if response.status_code == 200:
        result = response.json()
        return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Failed to generate summary.")
    else:
        return f"API Error: {response.json().get('error', {}).get('message', 'Unknown error')}"