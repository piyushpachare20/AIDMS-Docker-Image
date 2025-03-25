from fastapi import APIRouter, File, UploadFile, HTTPException
from .document_upload import process_document_upload

router = APIRouter()

@router.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    try:
        extracted_text = process_document_upload(file)
        return {"extracted_text": extracted_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))