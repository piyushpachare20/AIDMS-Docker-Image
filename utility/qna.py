from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pdfplumber
import os
import requests
from dotenv import load_dotenv

router = APIRouter()
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            extracted_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        if not extracted_text.strip():
            raise ValueError("No extractable text found in the PDF.")
        return extracted_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

def get_answer(question, context):
    data = {
        "contents": [{
            "parts": [{
                "text": f"Context:\n{context}\n\nQuestion: {question}\nPlease answer the question based on the context provided."
            }]
        }]
    }
    response = requests.post(API_URL, json=data)
    return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Failed to get answer.")

@router.post("/qna", summary="Question & Answer")
async def ask_question(
    file: UploadFile = File(..., description="Upload a PDF file"),
    question: str = Form(..., description="Enter your question")
):
    """Handles Q&A processing based on uploaded PDF."""
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        temp_path = f"temp/{file.filename}"
        os.makedirs("temp", exist_ok=True)
        
        with open(temp_path, "wb") as temp_file:
            temp_file.write(file.file.read())

        # Extract text from PDF
        context = extract_text_from_pdf(temp_path)
        answer = get_answer(question, context)

        # Cleanup
        os.remove(temp_path)

        return {"question": question, "answer": answer, "file": file.filename}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QnA Processing Error: {str(e)}")