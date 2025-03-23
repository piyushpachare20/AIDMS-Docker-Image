from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from helpers.constants import DATABASE_URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

# ✅ Database Connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database setup
Base = declarative_base()

# SQLAlchemy model for the activity log table
class ActivityLogDB(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    action = Column(String, index=True)
    document_id = Column(String)
    timestamp = Column(DateTime)

# ✅ Dependency to Get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
