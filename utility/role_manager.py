from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

ALLOWED_ROLES = ["admin", "editor", "viewer"]  # Define allowed roles

def change_user_role(email: str, new_role: str, db: Session, current_user: dict):
    """
    Change the role of a user.

    Args:
        email (str): The email of the user whose role is to be changed.
        new_role (str): The new role to assign to the user.
        db (Session): SQLAlchemy database session.
        current_user (dict): The current logged-in user's details.

    Returns:
        dict: A success message.
    """
    # Ensure the current user is an admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can change user roles.")

    # Validate the new role
    if new_role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Allowed roles are: {', '.join(ALLOWED_ROLES)}")

    # Check if the user exists
    user = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update the user's role
    db.execute(
        text("UPDATE users SET role = :role WHERE email = :email"),
        {"role": new_role, "email": email}
    )
    db.commit()

    return {"message": f"Role of user with email '{email}' updated to '{new_role}' successfully."}