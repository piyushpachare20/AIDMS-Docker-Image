from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text  # Import text
from fastapi import HTTPException
from datetime import datetime

def add_comment(db: Session, document_id: str, user_email: str, comment_text: str):
    """
    Add a comment to the database.

    Args:
        db (Session): SQLAlchemy database session.
        document_id (str): The ID of the document the comment is associated with.
        user_email (str): The email of the user making the comment.
        comment_text (str): The content of the comment.

    Returns:
        dict: A success message.
    """
    try:
        # SQL query to insert a new comment
        query = text("""
        INSERT INTO comments (document_id, user_email, comment_text, timestamp)
        VALUES (:document_id, :user_email, :comment_text, :timestamp)
        """)
        db.execute(query, {
            "document_id": document_id,
            "user_email": user_email,
            "comment_text": comment_text,
            "timestamp": datetime.now()
        })
        db.commit()
        return {"message": "Comment added successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")