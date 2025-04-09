from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from datetime import datetime
from helpers.database import ActivityLogDB, DocumentDB, UserDB  # Ensure these are correctly imported
from helpers.constants import DATE_FORMAT

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Fixed incorrect variable: _name -> __name__

# Updated Pydantic model
class ActivityLog(BaseModel):
    action: str = Field(..., description="Action performed by the user")
    document_name: Optional[str] = Field(None, description="Name of the document associated with the action")
    timestamp: str = Field(..., description="Timestamp of the action")


# Fetch document logs
def document_logs(db: Session) -> List[dict]:
    """
    Fetch logs with document_title, action, timestamp, and user_id.
    """
    try:
        logs_db = (
            db.query(ActivityLogDB, DocumentDB.title)
            .join(DocumentDB, ActivityLogDB.document_id == DocumentDB.document_id)
            .all()
        )

        logs = [
            {
                "document_title": log.title,  # From the joined DocumentDB table
                "action": log.ActivityLogDB.action,
                "timestamp": log.ActivityLogDB.timestamp.strftime(DATE_FORMAT),
                "user_id": log.ActivityLogDB.user_id,  # user_id from ActivityLogDB table
            }
            for log in logs_db
        ]
        return logs
    except Exception as e:
        logger.error(f"Error fetching document logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching document logs: {str(e)}")


# Fetch user logs
def user_logs(db: Session) -> List[dict]:
    """
    Fetch logs with user_id, username, action, and timestamp.
    """
    try:
        logs_db = (
            db.query(ActivityLogDB, UserDB.username)
            .join(UserDB, ActivityLogDB.user_id == UserDB.id)
            .all()
        )

        logs = [
            {
                "user_id": log.ActivityLogDB.user_id,
                "username": log.username,  # From the joined UserDB table
                "action": log.ActivityLogDB.action,
                "timestamp": log.ActivityLogDB.timestamp.strftime(DATE_FORMAT),
            }
            for log in logs_db
        ]
        return logs
    except Exception as e:
        logger.error(f"Error fetching user logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching user logs: {str(e)}")


# Fetch logs for a specific user
def fetch_logs(db: Session, user_id: int) -> List[dict]:
    """
    Fetch logs for a specific user by user_id.
    """
    try:
        logs_db = (
            db.query(ActivityLogDB, UserDB.username)
            .join(UserDB, ActivityLogDB.user_id == UserDB.id)
            .filter(ActivityLogDB.user_id == user_id)
            .all()
        )

        logs = [
            {
                "user_id": log.ActivityLogDB.user_id,
                "username": log.username,  # From the joined UserDB table
                "action": log.ActivityLogDB.action,
                "timestamp": log.ActivityLogDB.timestamp.strftime(DATE_FORMAT),
            }
            for log in logs_db
        ]
        return logs
    except Exception as e:
        logger.error(f"Error fetching logs for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching logs for user {user_id}: {str(e)}")


# Fetch all logs
def fetch_all_logs(db: Session) -> List[dict]:
    """
    Fetch all logs from the database, including user and document logs.
    """
    try:
        logs_db = (
            db.query(ActivityLogDB, UserDB.username, DocumentDB.title)
            .join(UserDB, ActivityLogDB.user_id == UserDB.id)
            .outerjoin(DocumentDB, ActivityLogDB.document_id == DocumentDB.document_id)
            .all()
        )

        logs = [
            {
                "user_id": log.ActivityLogDB.user_id,
                "username": log.username,  # From the joined UserDB table
                "action": log.ActivityLogDB.action,
                "document_title": log.title,  # From the joined DocumentDB table (if available)
                "timestamp": log.ActivityLogDB.timestamp.strftime(DATE_FORMAT),
            }
            for log in logs_db
        ]
        return logs
    except Exception as e:
        logger.error(f"Error fetching all logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching all logs: {str(e)}")


# Add a log entry to the database
def add_log_to_db(db: Session, user_id: int, log: ActivityLog) -> dict:
    """
    Add a log entry to the database.
    """
    try:
        new_log = ActivityLogDB(
            user_id=user_id,
            action=log.action,
            document_id=None,  # Set this if applicable
            timestamp=datetime.strptime(log.timestamp, DATE_FORMAT),
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return {
            "id": new_log.id,
            "user_id": new_log.user_id,
            "action": new_log.action,
            "timestamp": new_log.timestamp.strftime(DATE_FORMAT),
        }
    except Exception as e:
        logger.error(f"Error adding log to database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding log to database: {str(e)}")
