from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
from helpers.constants import SQLALCHEMY_DATABASE_URL # Import DATABASE_URL from constants

load_dotenv()  # Load environment variables from .env

# ✅ Database Connection
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ✅ Models
class ActivityLogDB(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String(255), index=True)
    document_id = Column(String(36), ForeignKey("documents.document_id"), nullable=True)  # ✅ Fix here
    timestamp = Column(DateTime)

class DocumentDB(Base):
    __tablename__ = "documents"
    document_id = Column(String(36), primary_key=True, index=True)  # ✅ UUID-style
    title = Column(String(255), nullable=False)

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False)

Base.metadata.create_all(bind=engine)


# ✅ Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
