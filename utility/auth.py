import hashlib
import random
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt
import smtplib
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from helpers.constants import SECRET_KEY, ALGORITHM, SENDER_EMAIL, APP_PASSWORD
from sqlalchemy.sql import text  # Import text for raw SQL queries

# Logging Setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Hash Password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Verify Password
def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password

# Generate JWT Token
def generate_jwt_token(email: str, role: str):
    payload = {
        "sub": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Send OTP Email
def send_otp_email(email: str, otp: str):
    subject = "OTP for Verification"
    body = f"Your OTP for verification is: {otp}"

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        logger.info(f"OTP email sent to {email}")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Error sending OTP email.")

# User Registration
def register_user(db: Session, username: str, email: str, password: str, role: str):
    email = email.strip().lower()

    # Use text() for raw SQL queries
    user = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    otp = str(random.randint(100000, 999999))
    hashed_password = hash_password(password)

    db.execute(
        text("INSERT INTO users (username, email, password, role, otp, verified) VALUES (:username, :email, :password, :role, :otp, :verified)"),
        {"username": username, "email": email, "password": hashed_password, "role": role, "otp": otp, "verified": False}
    )
    db.commit()

    send_otp_email(email, otp)
    return {"message": "OTP sent successfully"}

# Verify OTP
def verify_otp(db: Session, email: str, otp: str):
    email = email.strip().lower()
    otp = otp.strip()

    # Use text() for raw SQL queries
    user = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Access the tuple by index (6th column means index 5)
    user_otp = user[5]  # Adjusted to the correct index for 'otp'
    if user_otp != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    db.execute(text("UPDATE users SET verified = TRUE WHERE email = :email"), {"email": email})
    db.commit()

    return {"message": "Account verified successfully"}

# User Login
def login_user(db: Session, email: str, password: str):
    email = email.strip().lower()

    # Use text() for raw SQL queries
    user = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Access the tuple by index (adjust indices based on your table schema)
    user_password = user[3]  # 'password' is the 4th column in the 'users' table
    user_verified = user[6]  #  'verified' is the 7th column in the 'users' table
    user_role = user[4]      #  'role' is the 5th column in the 'users' table

    if not verify_password(password, user_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user_verified:
        raise HTTPException(status_code=400, detail="User not verified. Please verify your account.")

    token = generate_jwt_token(email, user_role)
    return {"access_token": token, "token_type": "bearer"}

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Return the decoded payload (e.g., user info)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")