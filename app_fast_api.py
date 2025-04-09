from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from helpers.database import get_db
from utility.search import search_documents
from utility.documents import (
    upload_document,
    get_document_metadata,
    download_document,
    edit_document_metadata,
    delete_document,
    DocumentMetadata
)
from utility.auth import register_user, verify_otp, login_user, get_current_user
from utility.view import fetch_all_documents
from utility.logs import fetch_all_logs, ActivityLog, document_logs, user_logs, fetch_logs, add_log_to_db
from utility.comments import add_comment
from typing import List, Literal
from typing import Optional

from utility.summarize_text import summarize_text, extract_text
from utility.translate_text import translate_text, process_text_input
from utility.transliteration import process_file_input, transliterate_text, clean_text
from utility.qna import get_answer, process_file
from utility.extract_text import process_document_upload
from utility.extract_images import extract_images_from_pdf

app = FastAPI(title="AI Document Processor and Management API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Search API
@app.get("/documents/search")
def search_endpoint(query: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        result = search_documents(query, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ✅ Upload Document API
@app.post("/documents/upload")
def upload_endpoint(
    file: UploadFile = File(...),
    title: str = Form(...),
    tags: List[str] = Form(...),
    permissions: List[str] = Form(...),
    uploaded_by: int = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    return upload_document(file, title, tags, permissions, uploaded_by, db)

# ✅ Get Document Metadata API
@app.get("/documents/{document_id}")
def get_metadata_endpoint(document_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_document_metadata(document_id, db)

# ✅ Download Document API
@app.get("/documents/download/{document_id}")
def download_endpoint(document_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return download_document(document_id, db)

# ✅ Edit Document Metadata API
@app.put("/documents/edit/{document_id}")
def edit_metadata_endpoint(document_id: str, metadata: DocumentMetadata, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return edit_document_metadata(document_id, metadata, db)

# ✅ Delete Document API
@app.delete("/documents/delete/{document_id}")
def delete_endpoint(document_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return delete_document(document_id, db)

# ✅ Fetch All Documents API
@app.get("/documents", summary="View/File Explorer")
def get_all_documents(db: Session = Depends(get_db)):
    """
    Endpoint to fetch all documents along with their metadata, tags, and comments.
    """
    try:
        documents = fetch_all_documents(db)
        return JSONResponse(content={"documents": documents}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"detail": str(e)}, status_code=500)

# ✅ User Registration Endpoint
@app.post("/auth/register")
async def register_user_endpoint(
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    return register_user(db, email)

# ✅ Verify OTP Endpoint
@app.post("/auth/verify-otp")
async def verify_otp_endpoint(
    email: str = Form(...),
    otp: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: Literal["editor", "viewer", "admin"] = Form(...),
    db: Session = Depends(get_db)
):
    return verify_otp(db, email, otp, username, password, role)

# ✅ User Login Endpoint
@app.post("/auth/login")
async def login_user_endpoint(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    return login_user(db, email, password)

# ✅ Fetch User Logs Endpoint (uses document_name now)
''''@app.get("/logs/user/{user_id}", response_model=List[ActivityLog])
async def get_user_logs(user_id: int, db: Session = Depends(get_db)):
    try:
        logs = fetch_logs(db, user_id)
        if not logs:
            raise HTTPException(status_code=404, detail=f"No logs found for user ID {user_id}")
        return logs
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")'''

# ✅ Add Log Endpoint (uses document_name now)
@app.post("/logs/user/{user_id}")
async def add_log(user_id: int, log: ActivityLog, db: Session = Depends(get_db)):
    return add_log_to_db(db, user_id, log)

# ✅ Fetch All Logs Endpoint (uses document_name now)
@app.get("/logs/all")
async def get_all_logs(db: Session = Depends(get_db)):
    return {"logs": fetch_all_logs(db)}

# ✅ Fetch Document Logs Endpoint
@app.get("/logs/documents")
async def get_document_logs(db: Session = Depends(get_db)):
    try:
        logs = document_logs(db)
        return {"logs": logs}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# ✅ Fetch User Logs Endpoint
@app.get("/logs/users")
async def get_user_logs(db: Session = Depends(get_db)):
    try:
        logs = user_logs(db)
        return {"logs": logs}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# ✅ Add Comment Endpoint
@app.post("/comments")
async def add_comment_endpoint(
    document_id: str,
    user_email: str,
    comment_text: str,
    db: Session = Depends(get_db)
):
    return add_comment(db, document_id, user_email, comment_text)

# ✅ Extract Text Endpoint
@app.post("/extract-text/")
async def extract_text_endpoint(file: UploadFile = File(...)):
    try:
        extracted_text = process_document_upload(file)
        return {"extracted_text": extracted_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Extract Images from PDF Endpoint
@app.post("/extract-images/")
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

# ✅ Translate Endpoint
@app.post("/translate/")
async def translate_endpoint(
    file: UploadFile = File(None),
    text: str = Form(None),
    target_language: str = Form(...),
    file_upload: bool = Form(...)
):
    extracted_text_list = process_text_input(file, text, file_upload)
    final_translation = translate_text(extracted_text_list, target_language)
    return {"translated_text": final_translation}

# ✅ Transliterate Endpoint
@app.post("/transliterate/")
async def transliterate_endpoint(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    target_script: str = Form(...),
    file_upload: bool = Form(...)
):
    extracted_text = process_file_input(file) if file_upload and file else text

    if not extracted_text or not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No text found to transliterate")

    result = transliterate_text(clean_text(extracted_text), target_script)
    return {"transliterated_text": result}

# ✅ QnA Endpoint
@app.post("/qna", summary="Question & Answer")
async def ask_question(
    file: UploadFile = File(..., description="Upload a PDF or DOCX file"),
    question: str = Form(..., description="Enter your question")
):
    """Handles Q&A processing based on uploaded PDF or DOCX."""
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
   
    context = process_file(file)
    if not context:
        raise HTTPException(status_code=400, detail="No extractable text found in the document.")
   
    answer = get_answer(question, context)
    return {"question": question, "answer": answer, "file": file.filename}

# ✅ Summarization Endpoint
@app.post("/summarize-text/")
async def summarize_text_endpoint(file: UploadFile = File(...)):
    """Handles file upload and calls summarization function."""
    if not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF or DOCX files only.")
   
    text = extract_text(file)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from the file.")
   
    summary = summarize_text(text)
    return {"summary": summary}

# ✅ Change Role API
@app.put("/auth/change-role")
async def change_role_endpoint(
    email: str = Form(..., description="Email of the user whose role is to be changed"),
    new_role: str = Form(..., description="New role to assign (admin, editor, viewer)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from utility.role_manager import change_user_role
    return change_user_role(email, new_role, db, current_user)

# ✅ Main entry point (fixed)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)