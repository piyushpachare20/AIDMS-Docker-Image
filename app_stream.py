import streamlit as st
import requests
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import text  # Import text for SQL queries
from utility.view import fetch_all_documents  # Import the fetch_all_documents function
from helpers.constants import DATABASE_URL  # Import the database URL
# Import necessary functions from documents.py
from utility.documents import upload_document, edit_document_metadata, get_document_metadata
import os  # Import os for file handling
from utility.documents import DocumentMetadata  # Import the DocumentMetadata class
from datetime import datetime  # Import datetime for timestamp generation

# Base URL of your FastAPI backend
BASE_URL = "http://127.0.0.1:8000"

# Set up the database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Welcome"

# Function to register a user
def register_user():
    st.title("📝 User Registration")
    st.markdown("Create a new account by filling in the details below.")
    username = st.text_input("👤 Username")
    email = st.text_input("📧 Email")
    password = st.text_input("🔑 Password", type="password")
    role = st.selectbox("🛠️ Role", ["user", "admin"])
    if st.button("Register"):
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "role": role
        }
        response = requests.post(f"{BASE_URL}/auth/register", data=payload)
        if response.status_code == 200:
            st.success("🎉 Registration successful! Please verify your email.")
        else:
            st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")

# Function to verify OTP
def verify_otp():
    st.title("🔑 Verify OTP")
    st.markdown("Enter the OTP sent to your email to verify your account.")
    email = st.text_input("📧 Email")
    otp = st.text_input("🔢 OTP")
    if st.button("Verify"):
        payload = {
            "email": email,
            "otp": otp
        }
        response = requests.post(f"{BASE_URL}/auth/verify-otp", data=payload)
        if response.status_code == 200:
            st.success("✅ OTP verified successfully!")
        else:
            st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")

# Function to log in a user
def login_user():
    st.title("Document Management System 🗂️📄📊")
    st.title("🔒 User Login")
    st.markdown("Welcome back! Please enter your credentials to log in.")
    email = st.text_input("📧 Email")
    password = st.text_input("🔑 Password", type="password")
    if st.button("Login"):
        payload = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/auth/login", data=payload)
        if response.status_code == 200:
            st.success("🎉 Login successful!")
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.auth_token = response.json().get("access_token")
            st.session_state.user_id = response.json().get("user_id")  # Store user ID
            st.write(f"Debug: User ID: {st.session_state.user_id}")  # Debug statement
        else:
            st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")

# Function to display the welcome page
def welcome_page():
    st.title("Welcome 🎉 👋 ✨!")
    st.write(f"Hello, {st.session_state.user_email}!")
    st.write("You are now logged in, Navigate to sidebar for using application.")

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    menu_option = st.sidebar.radio("Go to", [
        "Welcome", 
        "Search Documents", 
        "Delete Document", 
        "Upload Document", 
        "Edit Metadata", 
        "Get Metadata", 
        "Add Comment", 
        "Fetch All Logs", 
        "Add Log", 
        "Fetch User Logs", 
        "Download Document"  # New option
    ])

    if menu_option == "Welcome":
        st.session_state.current_page = "Welcome"
    elif menu_option == "Search Documents":
        st.session_state.current_page = "Search Documents"
    elif menu_option == "Delete Document":
        st.session_state.current_page = "Delete Document"
    elif menu_option == "Upload Document":
        st.session_state.current_page = "Upload Document"
    elif menu_option == "Edit Metadata":
        st.session_state.current_page = "Edit Metadata"
    elif menu_option == "Get Metadata":
        st.session_state.current_page = "Get Metadata"
    elif menu_option == "Add Comment":
        st.session_state.current_page = "Add Comment"
    elif menu_option == "Fetch All Logs":
        st.session_state.current_page = "Fetch All Logs"
    elif menu_option == "Add Log":
        st.session_state.current_page = "Add Log"
    elif menu_option == "Fetch User Logs":
        st.session_state.current_page = "Fetch User Logs"
    elif menu_option == "Download Document":  # Handle new option
        st.session_state.current_page = "Download Document"

    # Log Out Button
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.auth_token = None
        st.session_state.current_page = "Login"  # Redirect to login page
        st.success("You have been logged out.")

    # Navigate to the selected page
    if st.session_state.current_page == "Welcome":
        display_documents()
    elif st.session_state.current_page == "Search Documents":
        search_documents_ui()
    elif st.session_state.current_page == "Delete Document":
        delete_document_ui()
    elif st.session_state.current_page == "Upload Document":
        upload_document_ui()
    elif st.session_state.current_page == "Edit Metadata":
        edit_metadata_ui()
    elif st.session_state.current_page == "Get Metadata":
        get_metadata_ui()
    elif st.session_state.current_page == "Add Comment":
        add_comment_ui()
    elif st.session_state.current_page == "Fetch All Logs":
        fetch_all_logs_ui()
    elif st.session_state.current_page == "Add Log":
        add_log_ui()
    elif st.session_state.current_page == "Fetch User Logs":
        fetch_user_logs_ui()
    elif st.session_state.current_page == "Download Document":  # Navigate to new page
        download_document_ui()

# Function to display documents
def display_documents():
    #st.subheader("Documents")
    try:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        response = requests.get(f"{BASE_URL}/documents", headers=headers)
        if response.status_code == 200:
            documents = response.json()
            if documents:
                for doc in documents:
                    with st.expander(f"📄 {doc['title']} (ID: {doc['document_id']})"):
                        st.markdown(f"**Uploaded By:** {doc['uploaded_by']}")
                        st.markdown(f"**Tags:** {', '.join(doc['tags']) if doc['tags'] else 'No tags'}")
                        
                        st.markdown("### Comments:")
                        if doc['comments']:
                            for comment in doc['comments']:
                                st.markdown(f"- **{comment['user_email']}** at {comment['timestamp']}:")
                                st.markdown(f"  > {comment['comment_text']}")
                        else:
                            st.info("No comments available.")
            else:
                st.info("No documents found.")
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error fetching documents: {str(e)}")

# Function for Search Documents UI
def search_documents_ui():
    st.title("Search Documents🔍 📄")
    query = st.text_input("Enter search query")
    if st.button("Search"):
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        response = requests.get(f"{BASE_URL}/documents/search", params={"query": query}, headers=headers)
        if response.status_code == 200:
            results = response.json()
            if results:
                st.subheader("Search Results:")
                for index, doc in enumerate(results):  # Use enumerate to generate unique keys
                    with st.expander(f"📄 {doc['title']} (ID: {doc['document_id']})"):
                        st.markdown(f"**Uploaded By:** {doc['uploaded_by']}")
                        st.markdown(f"**Tags:** {doc['tags']}")

                        # Add a download button with a unique key
                        download_url = f"{BASE_URL}/documents/download/{doc['document_id']}"
                        download_response = requests.get(download_url, headers=headers)
                        if download_response.status_code == 200:
                            st.download_button(
                                label="Download Document",
                                data=download_response.content,
                                file_name=f"{doc['title']}.pdf",  # Adjust the file extension as needed
                                mime="application/pdf",  # Adjust MIME type based on the file type
                                key=f"download_button_{index}"  # Unique key for each button
                            )
                        else:
                            st.error("Unable to fetch the document for download.")
            else:
                st.info("No matching documents found.")
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
    if st.button("Back"):
        st.session_state.current_page = "Welcome"

# Function for Delete Document UI
def delete_document_ui():
    st.title("Delete Document🗑️ ❌")
    document_id = st.text_input("Enter Document ID to delete")
    if st.button("Delete"):
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        response = requests.delete(f"{BASE_URL}/documents/delete/{document_id}", headers=headers)
        if response.status_code == 200:
            st.success("Document deleted successfully!")
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
    if st.button("Back"):
        st.session_state.current_page = "Welcome"

# Function for Upload Document UI
def upload_document_ui():
    st.title("Upload Document📤 🆙")
    title = st.text_input("Enter Document Title")
    uploaded_file = st.file_uploader("Choose a file")
    tags = st.text_input("Enter tags (comma-separated)")
    permissions = st.text_input("Enter permissions (comma-separated)")

    # Fetch user_id from the database using the logged-in user's email
    db = SessionLocal()
    try:
        user_query = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": st.session_state.user_email}
        )
        user = user_query.fetchone()
        if user:
            uploaded_by = str(user[0])  # Convert user_id to string
        else:
            st.error("Error: User not found in the database.")
            return
    except Exception as e:
        st.error(f"Error fetching user ID: {str(e)}")
        return
    finally:
        db.close()

    # Display the fetched user_id in the UI
    st.text_input("Uploaded By (User ID)", value=uploaded_by, disabled=True)  # Read-only field for debugging

    if uploaded_file is not None and st.button("Upload"):
        try:
            # Convert tags and permissions to lists
            tags_list = [tag.strip() for tag in tags.split(",")] if tags else []
            permissions_list = [perm.strip() for perm in permissions.split(",")] if permissions else []

            # Prepare the payload for the backend
            files = {"file": uploaded_file}
            data = {
                "title": title,
                "tags": tags_list,  # Send tags as a list
                "permissions": permissions_list,  # Send permissions as a list
                "uploaded_by": uploaded_by,
            }
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

            # Send the request to the backend
            response = requests.post(f"{BASE_URL}/documents/upload", files=files, data=data, headers=headers)

            if response.status_code == 200:
                st.success("Document uploaded successfully!")
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error uploading document: {str(e)}")
    if st.button("Back"):
        st.session_state.current_page = "Welcome"

# Function for Edit Metadata UI
def edit_metadata_ui():
    st.title("Edit Metadata✏️ 🛠️")
    document_id = st.text_input("Enter Document ID")
    
    # Dropdown for metadata keys
    metadata_key = st.selectbox(
        "Select Metadata Key",
        ["title", "tags", "permissions"]  # Update this list based on documents.py
    )
    
    metadata_value = st.text_input("Enter Metadata Value")
    
    if st.button("Update Metadata"):
        db = SessionLocal()  # Create a database session
        try:
            # Create a DocumentMetadata object with the selected metadata key
            metadata = DocumentMetadata(
                title=metadata_value if metadata_key == "title" else None,
                tags=[metadata_value] if metadata_key == "tags" else None,
                permissions=[metadata_value] if metadata_key == "permissions" else None
            )
            
            # Call the edit_document_metadata function
            response = edit_document_metadata(document_id, metadata, db=db)

            if response["message"] == "Metadata updated successfully":
                st.success("Metadata updated successfully!")
            else:
                st.error("Error: Unknown error occurred.")
        except Exception as e:
            st.error(f"Error updating metadata: {str(e)}")
        finally:
            db.close()  # Ensure the session is closed
    
    if st.button("Back"):
        st.session_state.current_page = "Welcome"

# Function for Get Metadata UI
def get_metadata_ui():
    st.title("Get Metadata📋 🗂️")
    document_id = st.text_input("Enter Document ID")
    if st.button("Fetch Metadata"):
        db = SessionLocal()  # Create a database session
        try:
            response = get_document_metadata(document_id, db)  # Pass the session to the function
            if response:
                st.subheader("Document Metadata")
                st.markdown(f"**Title:** {response.get('title', 'N/A')}")
                st.markdown(f"**Uploaded By:** {response.get('uploaded_by', 'N/A')}")
                
                # Display tags
                tags = response.get('tags', [])
                if tags:
                    st.markdown("**Tags:**")
                    for tag in tags:
                        st.markdown(f"- {tag}")
                else:
                    st.markdown("**Tags:** No tags available")
                
                # Display permissions
                permissions = response.get('permissions', [])
                if permissions:
                    st.markdown("**Permissions:**")
                    for permission in permissions:
                        st.markdown(f"- {permission}")
                else:
                    st.markdown("**Permissions:** No permissions available")
            else:
                st.error("No metadata found for the given Document ID.")
        except Exception as e:
            st.error(f"Error fetching metadata: {str(e)}")
        finally:
            db.close()  # Ensure the session is closed
    if st.button("Back"):
        st.session_state.current_page = "Welcome"

# Function for Add Comment UI
def add_comment_ui():
    st.title("Add Comment💬 📝")
    document_id = st.text_input("Enter Document ID")
    comment = st.text_area("Enter your comment")

    if st.button("Submit Comment"):
        try:
            # Prepare the query parameters for the backend
            params = {
                "document_id": document_id,
                "user_email": st.session_state.user_email,  # Fetch the user email from session state
                "comment_text": comment
            }
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

            # Send the request to the backend
            response = requests.post(f"{BASE_URL}/comments", params=params, headers=headers)

            if response.status_code == 200:
                st.success("Comment added successfully!")
            elif response.status_code == 404:
                st.error("Error: The requested endpoint was not found. Please check the backend.")
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error adding comment: {str(e)}")

    if st.button("Back"):
        st.session_state.current_page = "Welcome"

# Function for Fetch All Logs UI
def fetch_all_logs_ui():
    st.title("Fetch All Logs📜 📊")
    if st.button("Fetch Logs"):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
            response = requests.get(f"{BASE_URL}/logs/all", headers=headers)

            if response.status_code == 200:
                logs = response.json().get("logs", [])
                if logs:
                    st.subheader("Logs:")
                    for log in logs:
                        st.markdown("---")  # Add a horizontal line for separation
                        st.markdown(f"**Action:** {log.get('action', 'N/A')}")
                        st.markdown(f"**Document ID:** {log.get('document_id', 'N/A')}")
                        st.markdown(f"**Timestamp:** {log.get('timestamp', 'N/A')}")
                else:
                    st.info("No logs found.")
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error fetching logs: {str(e)}")

    if st.button("Back"):
        st.session_state.current_page = "Welcome"

# Function for Add Log UI
def add_log_ui():
    st.title("Add Log➕ 🗒️")
    
    # Fetch user_id from the database using the logged-in user's email
    db = SessionLocal()
    try:
        user_query = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": st.session_state.user_email}
        )
        user = user_query.fetchone()
        if user:
            user_id = str(user[0])  # Convert user_id to string
        else:
            st.error("Error: User not found in the database.")
            return
    except Exception as e:
        st.error(f"Error fetching user ID: {str(e)}")
        return
    finally:
        db.close()

    # Display the fetched user_id in the UI
    st.text_input("User ID", value=user_id, disabled=True)  # Read-only field for debugging

    # Input fields for action and document ID
    action = st.text_input("Enter Action (e.g., upload, delete, etc.)")
    document_id = st.text_input("Enter Document ID (if applicable)")

    # Automatically generate the current timestamp
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.text_input("Timestamp (Auto-filled)", value=current_timestamp, disabled=True)  # Read-only field for timestamp

    if st.button("Submit Log"):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
            data = {
                "action": action,  # Include the action field
                "document_id": document_id,  # Include the document_id field
                "timestamp": current_timestamp  # Use the auto-filled timestamp
            }
            response = requests.post(f"{BASE_URL}/logs/user/{user_id}", json=data, headers=headers)

            if response.status_code == 200:
                st.success("Log added successfully!")
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error adding log: {str(e)}")

    if st.button("Back"):
        st.session_state.current_page = "Welcome"

# Function for Fetch User Logs UI
def fetch_user_logs_ui():
    st.title("Fetch User Logs👤 📜")
    
    # Fetch user_id from the database using the logged-in user's email
    db = SessionLocal()
    try:
        user_query = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": st.session_state.user_email}
        )
        user = user_query.fetchone()
        if user:
            user_id = str(user[0])  # Convert user_id to string
        else:
            st.error("Error: User not found in the database.")
            return
    except Exception as e:
        st.error(f"Error fetching user ID: {str(e)}")
        return
    finally:
        db.close()

    # Display the fetched user_id in the UI
    st.text_input("User ID", value=user_id, disabled=True)  # Read-only field for debugging

    if st.button("Fetch Logs"):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
            response = requests.get(f"{BASE_URL}/logs/user/{user_id}", headers=headers)

            if response.status_code == 200:
                logs = response.json()
                if logs:
                    st.subheader("User Logs:")
                    for log in logs:
                        st.markdown("---")  # Add a horizontal line for separation
                        st.markdown(f"**Action:** {log.get('action', 'N/A')}")
                        document_id = log.get('document_id', 'N/A')
                        if document_id:
                            st.markdown(f"**Document ID:** {document_id}")
                        else:
                            st.markdown("**Document ID:** Not available")
                        st.markdown(f"**Timestamp:** {log.get('timestamp', 'N/A')}")
                else:
                    st.info("No logs found for this user.")
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error fetching user logs: {str(e)}")

    if st.button("Back"):
        st.session_state.current_page = "Welcome"

def download_document_ui():
    st.title("Download Document📥 ⬇️")
    document_id = st.text_input("Enter Document ID")
    if st.button("Download"):
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        download_url = f"{BASE_URL}/documents/download/{document_id}"
        try:
            # Request the document from the backend
            download_response = requests.get(download_url, headers=headers, stream=True)

            if download_response.status_code == 200:
                # Provide a download button for the document
                st.download_button(
                    label="Download Document",
                    data=download_response.content,
                    file_name=f"{document_id}.pdf",  # Adjust the file extension as needed
                    mime="application/pdf"  # Adjust MIME type based on the file type
                )
            else:
                # Handle errors returned by the backend
                try:
                    error_detail = download_response.json().get('detail', 'Unable to fetch the document.')
                    st.error(f"Error: {error_detail}")
                except ValueError:
                    st.error("Error: Invalid response from the server.")
        except Exception as e:
            st.error(f"Error fetching the document: {str(e)}")
    if st.button("Back"):
        st.session_state.current_page = "Welcome"

# Main function to render the Streamlit app
def main():
    if st.session_state.logged_in:
        # Show the welcome page if the user is logged in
        welcome_page()
    else:
        # Show authentication options if the user is not logged in
        st.sidebar.title("Authentication")
        option = st.sidebar.selectbox("Choose an option", ["Login", "Register", "Verify OTP"])

        if option == "Login":
            login_user()
        elif option == "Register":
            register_user()
        elif option == "Verify OTP":
            verify_otp()

if __name__ == "__main__":
    main()