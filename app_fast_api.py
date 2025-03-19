from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from helpers.database import get_db
from utility.search import search_documents
from utility.documents import (
    upload_document,
    get_document_metadata,
    download_document,
    edit_document_metadata,
    delete_document,
    DocumentMetadata  # Import DocumentMetadata here
)
from utility.auth import register_user, verify_otp, login_user, get_current_user
from utility.view import fetch_all_documents  # Import the new function
from typing import List

app = FastAPI()

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
@app.get("/documents")
def get_documents(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return fetch_all_documents(db)

# ✅ User Registration Endpoint
@app.post("/auth/register")
async def register_user_endpoint(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    return register_user(db, username, email, password, role)

# ✅ Verify OTP Endpoint
@app.post("/auth/verify-otp")
async def verify_otp_endpoint(
    email: str = Form(...),
    otp: str = Form(...),
    db: Session = Depends(get_db)
):
    return verify_otp(db, email, otp)

# ✅ User Login Endpoint
@app.post("/auth/login")
async def login_user_endpoint(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    return login_user(db, email, password)

# ✅ Run using:
# uvicorn app_fast_api:app --reload