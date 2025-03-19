from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from helpers.constants import DATABASE_URL

# ✅ Database Connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Dependency to Get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
