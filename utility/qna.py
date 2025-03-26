from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import os
import requests
import pdfplumber
import docx
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        return text.strip() if text.strip() else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction error: {str(e)}")

def extract_text_from_docx(docx_path):
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip() if text.strip() else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX extraction error: {str(e)}")

def get_answer(question, context):
    """Sends a request to the AI API to get an answer based on the context."""
    data = {
        "contents": [{
            "parts": [{
                "text": f"Context:\n{context}\n\nQuestion: {question}\nAnswer based only on the provided context."
            }]
        }]
    }
    response = requests.post(API_URL, json=data)
    return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Failed to get answer.")

def process_file(file: UploadFile):
    """Handles file saving and text extraction."""
    file_ext = file.filename.split(".")[-1].lower()
    temp_path = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)
   
    with open(temp_path, "wb") as temp_file:
        temp_file.write(file.file.read())
   
    if file_ext == "pdf":
        text = extract_text_from_pdf(temp_path)
    elif file_ext == "docx":
        text = extract_text_from_docx(temp_path)
    else:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and DOCX are allowed.")
   
    os.remove(temp_path)
    return text