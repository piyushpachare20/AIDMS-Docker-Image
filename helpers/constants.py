import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")  # Changed from 'db' to 'localhost' for local development
MYSQL_PORT = os.getenv("MYSQL_PORT", 3306)
MYSQL_DB = os.getenv("MYSQL_DATABASE")

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
SENDER_EMAIL = "patilatharva1214@gmail.com"
APP_PASSWORD = "aqpa iekp mcrb ctdr"
LOGGING_LEVEL = "INFO"
ACTIVITY_LOGS_TABLE = "activity_logs"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
