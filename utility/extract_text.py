from fastapi import FastAPI, File, UploadFile, HTTPException
from pdfminer.high_level import extract_text
import docx
import requests
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# Initialize FastAPI app
app = FastAPI()

# Function to clean and merge broken lines without adding excessive paragraph breaks
def clean_extracted_text(text):
    text = re.sub(r'\n(?=[a-z])', ' ', text)  # Merge broken lines mid-sentence
    text = re.sub(r'\n{2,}', '\n', text)  # Ensure proper paragraph separation
    return text.strip()

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    try:
        text = extract_text(file_path)
        return clean_extracted_text(text) if text else ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")

# Function to extract text from DOCX
def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from DOCX: {str(e)}")

# Process document upload
def process_document_upload(file: UploadFile):
    file_path = f"temp_{file.filename}"
    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())  # Save the uploaded file temporarily

        if file.filename.endswith(".pdf"):
            extracted_text = extract_text_from_pdf(file_path)
        elif file.filename.endswith(".docx"):
            extracted_text = extract_text_from_docx(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format! Only PDF and DOCX are allowed.")
       
        return extracted_text
    finally:
        os.remove(file_path)  # Clean up temp file