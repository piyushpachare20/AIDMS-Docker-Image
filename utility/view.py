from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

def fetch_all_documents(db: Session):
    try:
        documents = db.execute(text("""
            SELECT d.document_id, d.title, u.email
            FROM documents d
            JOIN users u ON d.uploaded_by = u.id
        """)).fetchall()  # Fetch results as tuples

        if not documents:
            raise HTTPException(status_code=404, detail="No documents found")

        document_list = []
        for doc in documents:
            doc_id = doc[0]  # Use index instead of doc["document_id"]
            title = doc[1]
            uploaded_by_email = doc[2]  # Fetch uploader's email
            
            # Fetch tags for each document
            tags = db.execute(
                text("""
                    SELECT t.tag_name FROM tags t
                    JOIN document_tags dt ON t.tag_id = dt.tag_id
                    WHERE dt.document_id = :document_id
                """),
                {"document_id": doc_id}
            ).fetchall()

            tag_names = [tag[0] for tag in tags]  # Fetch tag names correctly

            document_list.append({
                "document_id": doc_id,
                "title": title,
                "tags": tag_names,
                "uploaded_by": uploaded_by_email  # Email instead of ID
            })

        return document_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")