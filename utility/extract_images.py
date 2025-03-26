import fitz  # PyMuPDF
from docx import Document
import io
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
import base64
from io import BytesIO
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

app = FastAPI()

def extract_images_from_pdf(file_content):
    pdf_document = fitz.open(stream=file_content, filetype="pdf")
    images = []
   
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        image_list = page.get_images()
       
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
           
            # Convert to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            images.append(f"data:image/png;base64,{image_base64}")
   
    return images

def extract_images_from_docx(file):
    doc = Document(file)
    images = []
   
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            images.append(image_base64)
   
    return images

def get_answer(question, context):
    """Sends a request to the Gemini API to get an answer based on the extracted context."""
    data = {
        "contents": [{
            "parts": [{
                "text": f"Context:\n{context}\n\nQuestion: {question}\nPlease answer the question based on the context provided."
            }]
        }]
    }
    response = requests.post(API_URL, json=data)
    return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Failed to get answer.")