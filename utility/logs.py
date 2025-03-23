from pydantic import BaseModel
from typing import List
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from datetime import datetime
from helpers.database import ActivityLogDB  # Import database models from database.py
from helpers.constants import DATE_FORMAT  # Import constants from constants.py

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the Pydantic model for user activity log
class ActivityLog(BaseModel):
    action: str
    document_id: str
    timestamp: str

# Function to fetch logs from the database
def fetch_logs(db: Session, user_id: int) -> List[ActivityLog]:
    try:
        logs_db = db.query(ActivityLogDB).filter(ActivityLogDB.user_id == user_id).all()
        logs = [
            ActivityLog(
                action=log.action,
                document_id=log.document_id or "",  # Ensure document_id is a string
                timestamp=log.timestamp.strftime(DATE_FORMAT)  # Use constant for date format
            )
            for log in logs_db
        ]
        return logs
    except SQLAlchemyError as e:
        logger.error(f"Database error in fetch_logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

# Function to add a log to the database
def add_log_to_db(db: Session, user_id: int, log: ActivityLog):
    try:
        new_log = ActivityLogDB(
            user_id=user_id,
            action=log.action,
            document_id=log.document_id,
            timestamp=datetime.strptime(log.timestamp, DATE_FORMAT)  # Use constant for date format
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        logger.info(f"Log added successfully for user ID {user_id}")
        return {"message": "Log added successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error adding log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding log: {str(e)}")

# Function to fetch all logs from the database
def fetch_all_logs(db: Session) -> List[ActivityLog]:
    try:
        logs_db = db.query(ActivityLogDB).all()
        logs = [
            ActivityLog(
                action=log.action,
                document_id=log.document_id or "",  # Ensure document_id is a string
                timestamp=log.timestamp.strftime(DATE_FORMAT)  # Use constant for date format
            )
            for log in logs_db
        ]
        return logs
    except Exception as e:
        logger.error(f"Error fetching all logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching all logs: {str(e)}")