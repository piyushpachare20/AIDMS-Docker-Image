from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

def fetch_all_documents(db: Session):
    try:
        # Fetch documents along with the uploader's email
        documents = db.execute(text("""
            SELECT d.document_id, d.title, u.email
            FROM documents d
            JOIN users u ON d.uploaded_by = u.id
        """)).fetchall()

        if not documents:
            return []

        document_list = []
        for doc in documents:
            doc_id = doc[0]
            title = doc[1]
            uploaded_by_email = doc[2]

            # Fetch tags for each document
            tags = db.execute(
                text("""
                    SELECT t.tag_name FROM tags t
                    JOIN document_tags dt ON t.tag_id = dt.tag_id
                    WHERE dt.document_id = :document_id
                """),
                {"document_id": doc_id}
            ).fetchall()

            tag_names = [tag[0] for tag in tags]

            # Fetch comments for each document
            comments = db.execute(
                text("""
                    SELECT c.comment_text, c.user_email, c.timestamp
                    FROM comments c
                    WHERE c.document_id = :document_id
                """),
                {"document_id": doc_id}
            ).fetchall()

            comment_list = [
                {
                    "comment_text": comment[0],
                    "user_email": comment[1],
                    "timestamp": comment[2].strftime('%Y-%m-%d %H:%M:%S')
                }
                for comment in comments
            ]

            document_list.append({
                "document_id": doc_id,
                "title": title,
                "tags": tag_names,
                "uploaded_by": uploaded_by_email,
                "comments": comment_list
            })

        print(document_list)  # Debug print to verify the data
        return document_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")