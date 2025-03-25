from pdfminer.high_level import extract_text
import docx
import requests
from dotenv import load_dotenv
import os
import re

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# Function to clean and merge broken lines without adding excessive paragraph breaks
def clean_extracted_text(text):
    text = re.sub(r'\n(?=[a-z])', ' ', text)  # Merge broken lines mid-sentence
    text = re.sub(r'\n{2,}', '\n', text)  # Ensure proper paragraph separation
    return text.strip()

# Function to extract text from PDF using pdfminer
def extract_text_from_pdf(uploaded_file):
    try:
        text = extract_text(uploaded_file)
        return clean_extracted_text(text) if text else ""
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

# Function to extract text from DOCX
def extract_text_from_docx(uploaded_file):
    try:
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Error extracting text from DOCX: {str(e)}"

# Process document upload
def process_document_upload(file):
    if file.filename.endswith(".pdf"):
        return extract_text_from_pdf(file.file)
    elif file.filename.endswith(".docx"):
        return extract_text_from_docx(file.file)
    else:
        return "Unsupported file format!"