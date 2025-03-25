from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import requests
import os
import re
from typing import Optional
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import docx
from dotenv import load_dotenv

router = APIRouter()
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
    laparams = LAParams(detect_vertical=False, all_texts=True)  # Improved layout parsing
    text = extract_text(file_path, laparams=laparams)
    return clean_text(text)

def transliterate_text(text: str, target_language: str):
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
                    "temperature": 0.0,  # Ensure deterministic output
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

@router.post("/transliterate/")
async def transliterate_endpoint(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    target_script: str = Form(...),
    file_upload: bool = Form(...)
):
    try:
        if file_upload and file:
            file_path = f"temp_{file.filename}"
            with open(file_path, "wb") as f:
                f.write(await file.read())  # Save the uploaded file
            
            if file.filename.endswith('.pdf'):
                text = extract_text_from_pdf(file_path)
            elif file.filename.endswith('.docx'):
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and DOCX are allowed.")
            
            os.remove(file_path)  # Clean up temp file

        elif not text:
            raise HTTPException(status_code=400, detail="Either file or text must be provided")
        
        text = clean_text(text)  # Clean extracted text before transliteration
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found to transliterate")
            
        result = transliterate_text(text, target_script)
        return {"transliterated_text": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))