import pdfplumber
import docx
import requests
from ratelimit import limits, sleep_and_retry
from dotenv import load_dotenv
import os
import json
from fastapi import APIRouter, File, UploadFile, HTTPException
from utility.translate_text import call_api
router = APIRouter()

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

@router.post("/summarize-text/")
async def summarize_text_endpoint(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided.")
    try:
        if file.filename.endswith(('.pdf', '.docx')):
            text = ""
            if file.filename.endswith('.pdf'):
                text = "\n".join(extract_text_from_pdf(file.file))
            else:
                text = "\n".join(extract_text_from_docx(file.file))
            
            if not text.strip():
                raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

            response = requests.post(
                API_URL,
                json={
                    "contents": [{
                        "parts": [{"text": f"Please provide a concise summary of the following text:\n\n{text}"}]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 1024
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    summary = result["candidates"][0]["content"]["parts"][0]["text"]
                    return {"summary": summary}
                else:
                    raise HTTPException(status_code=500, detail="No summary generated")
            else:
                error_message = response.json().get("error", {}).get("message", "Unknown error")
                raise HTTPException(status_code=response.status_code, detail=f"API Error: {error_message}")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF or DOCX files only.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Extract text from PDF
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        extracted_text = [page.extract_text() or "" for page in pdf.pages]
        print("📄 Extracted Text from PDF:", extracted_text)  # Debugging
        return extracted_text

# Extract text from DOCX
def extract_text_from_docx(uploaded_file):
    doc = docx.Document(uploaded_file)
    extracted_text = ["\n".join([para.text for para in doc.paragraphs])]
    print("📄 Extracted Text from DOCX:", extracted_text)  # Debugging
    return extracted_text

# Summarize text using Gemini API
def summarize_text(text):
    if not text.strip():
        return "⚠ No text found to summarize."
    
    # Debugging: Log the text being sent
    print("✉ Text Sent to API:", text)
    
    data = {"contents": [{"parts": [{"text": f"Summarize this:\n{text}"}]}]}
    return call_api(data)

# Summarization process
def summarize_text_page(file):
    try:
        if file.filename.endswith(".pdf"):
            extracted_text = extract_text_from_pdf(file.file)
        elif file.filename.endswith(".docx"):
            extracted_text = extract_text_from_docx(file.file)
        else:
            return "⚠ Unsupported file format!"

        # Return the summary of all pages combined (or per page depending on structure)
        summarized_text = "\n".join([summarize_text(page) for page in extracted_text if page.strip()])
        return summarized_text
    
    except Exception as e:
        return f"❌ Error processing file: {str(e)}"