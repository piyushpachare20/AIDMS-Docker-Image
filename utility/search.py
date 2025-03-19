from sqlalchemy.orm import Session
from sqlalchemy import text

def search_documents(query: str, db: Session):
    if not query:
        return {"error": "Query parameter is required."}

    # ✅ SQL Query to Search by Title, Tag, or Uploaded By (Email)
    sql_query = """
    SELECT d.document_id, d.title, GROUP_CONCAT(t.tag_name) AS tags, u.email AS uploaded_by
    FROM documents d
    JOIN users u ON d.uploaded_by = u.id
    LEFT JOIN document_tags dt ON d.document_id = dt.document_id
    LEFT JOIN tags t ON dt.tag_id = t.tag_id
    WHERE LOWER(d.title) LIKE LOWER(:query)
    OR LOWER(t.tag_name) LIKE LOWER(:query)
    OR LOWER(u.email) LIKE LOWER(:query)
    GROUP BY d.document_id, d.title, u.email;
    """

    # ✅ Execute Query
    result = db.execute(text(sql_query), {"query": f"%{query}%"}).mappings().all()

    return result if result else {"message": "No documents found."}
