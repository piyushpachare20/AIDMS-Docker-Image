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
from utility.logs import fetch_logs, add_log_to_db, fetch_all_logs, ActivityLog  # Import logs functions and model
from utility.comments import add_comment  # Import add_comment function
from typing import List, Literal

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
    role: Literal["editor", "viewer", "admin"] = Form(...),  # Restrict role to specific values
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

# ✅ Fetch User Logs Endpoint
@app.get("/logs/user/{user_id}", response_model=List[ActivityLog])
async def get_user_logs(user_id: int, db: Session = Depends(get_db)):
    try:
        logs = fetch_logs(db, user_id)
        if not logs:
            raise HTTPException(status_code=404, detail=f"No logs found for user ID {user_id}")
        return logs
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# ✅ Add Log Endpoint
@app.post("/logs/user/{user_id}")
async def add_log(user_id: int, log: ActivityLog, db: Session = Depends(get_db)):
    return add_log_to_db(db, user_id, log)

# ✅ Fetch All Logs Endpoint
@app.get("/logs/all")
async def get_all_logs(db: Session = Depends(get_db)):
    return {"logs": fetch_all_logs(db)}

# ✅ Add Comment Endpoint
@app.post("/comments")
async def add_comment_endpoint(
    document_id: str,
    user_email: str,
    comment_text: str,
    db: Session = Depends(get_db)
):
    return add_comment(db, document_id, user_email, comment_text)

# ✅ Run using:
# uvicorn app_fast_api:app --reload