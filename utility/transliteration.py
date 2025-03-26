from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import requests
import os
import re
from typing import Optional
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import docx
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

def clean_text(text: str):
    """Removes unnecessary line breaks and ensures proper spacing."""
    text = re.sub(r"\n\s*\n", "\n\n", text)  # Preserve paragraph breaks
    text = re.sub(r"([^\n])\n([^\n])", r"\1 \2", text)  # Remove inline breaks
    text = re.sub(r"\s+", " ", text)  # Normalize spaces
    return text.strip()

def extract_text_from_pdf(file_path: str):
    """Extracts text from a PDF, handling multi-column formats correctly."""
    laparams = LAParams(detect_vertical=False, all_texts=True)
    text = extract_text(file_path, laparams=laparams)
    return clean_text(text)

def extract_text_from_docx(file_path: str):
    """Extracts text from a DOCX file."""
    doc = docx.Document(file_path)
    return clean_text("\n".join([para.text for para in doc.paragraphs]))

def process_file_input(file: UploadFile):
    """Processes file input, extracts text, and removes temporary file."""
    if not file:
        return None
   
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())  # Save the uploaded file
   
    if file.filename.endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file.filename.endswith('.docx'):
        text = extract_text_from_docx(file_path)
    else:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and DOCX are allowed.")
   
    os.remove(file_path)  # Clean up temp file
    return text

def transliterate_text(text: str, target_language: str):
    """Calls the API to transliterate text into the target script."""
    if not API_KEY:
        raise HTTPException(status_code=400, detail="API Key is missing!")

    prompt = f"""
    Transliterate the following text to {target_language} script while keeping the pronunciation intact.
   
    IMPORTANT:
    - DO NOT TRANSLATE the meaning, only convert the script.
    - Maintain all punctuation and formatting exactly as in the original text.
    - Preserve proper nouns, technical terms, and abbreviations as they are.
   
    Text: {text}
    """

    try:
        response = requests.post(
            API_URL,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": 2048
                }
            }
        )
       
        response.raise_for_status()
        result = response.json()
       
        if "candidates" in result and len(result["candidates"]) > 0:
            return clean_text(result["candidates"][0]["content"]["parts"][0]["text"])
        else:
            raise HTTPException(status_code=500, detail="No transliteration generated")
   
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")