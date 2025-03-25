import fitz  # PyMuPDF
from docx import Document
import io
from PIL import Image
from fastapi import APIRouter, File, UploadFile, HTTPException
import fitz
import base64
from io import BytesIO

router = APIRouter()

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

@router.post("/extract-images/")
async def extract_images_endpoint(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        if file.filename.endswith(".pdf"):
            images = extract_images_from_pdf(contents)
            return {"images": images}
        else:
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_images_from_docx(file):
    doc = Document(file)
    images = []
    
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            images.append(image_base64)
    
    return images