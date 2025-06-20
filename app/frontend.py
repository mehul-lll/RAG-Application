import streamlit as st
import requests
from datetime import datetime, timedelta
import os
import time

BACKEND_URL = "http://localhost:8000"
TOKEN_FILE = "token.txt"

# Token persistence functions
def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    return None

def clear_token():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = load_token()

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'user_documents' not in st.session_state:
    st.session_state.user_documents = []

if 'show_documents' not in st.session_state:
    st.session_state.show_documents = False

if 'selected_date' not in st.session_state:
    st.session_state.selected_date = "Today"

if 'current_chat' not in st.session_state:
    st.session_state.current_chat = []

def get_user_documents():
    """Fetch the user's documents from the backend API"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/documents",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            st.session_state.user_documents = response.json()
            return True, "Documents loaded"
        else:
            return False, response.json().get("detail", "Failed to load documents")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

# Auto-fetch user if token exists
if st.session_state.token and not st.session_state.current_user:
    try:
        user_response = requests.get(
            f"{BACKEND_URL}/users/me",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if user_response.status_code == 200:
            st.session_state.current_user = user_response.json()
            get_user_documents()
        else:
            clear_token()
            st.session_state.token = None
    except:
        clear_token()
        st.session_state.token = None

def register_user(username, email, password):
    try:
        response = requests.post(
            f"{BACKEND_URL}/register",
            json={"username": username, "email": email, "password": password}
        )
        if response.status_code == 200:
            return True, "Registration successful! Please login."
        else:
            return False, response.json().get("detail", "Registration failed")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def login_user(username, password):
    try:
        response = requests.post(
            f"{BACKEND_URL}/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            st.session_state.token = token
            save_token(token)

            user_response = requests.get(
                f"{BACKEND_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if user_response.status_code == 200:
                st.session_state.current_user = user_response.json()
                get_user_documents()
            return True, "Login successful!"
        else:
            return False, "Invalid username or password"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def delete_document(document_name):
    """Delete a document from the backend"""
    try:
        import urllib.parse
        encoded_name = urllib.parse.quote(document_name)
        
        response = requests.delete(
            f"{BACKEND_URL}/documents/{encoded_name}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            get_user_documents()
            return True, response.json()["message"]
        else:
            return False, response.json().get("detail", "Failed to delete document")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def upload_file(file):
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(
            f"{BACKEND_URL}/upload-file",
            files=files,
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            get_user_documents()
            return True, response.json()["message"]
        else:
            return False, response.json().get("detail", "Upload failed")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def send_query(query_text):
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"text": query_text},
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            result = response.json()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            chat_entry = {
                "timestamp": timestamp,
                "user_query": query_text,
                "bot_response": result["answer"],
                "sources": result["sources"]
            }
            st.session_state.chat_history.append(chat_entry)
            st.session_state.current_chat.append(chat_entry)
            return True, result
        else:
            return False, response.json().get("detail", "Query failed")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def get_chat_history():
    try:
        response = requests.get(
            f"{BACKEND_URL}/chat-history",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            history = response.json()
            formatted_history = []
            for item in history:
                formatted_history.append({
                    "timestamp": item["timestamp"],
                    "user_query": item["user_query"],
                    "bot_response": item["bot_response"],
                    "sources": []
                })
            st.session_state.chat_history = formatted_history[::-1]
            return True, "History loaded"
        else:
            return False, response.json().get("detail", "Failed to load history")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def group_history_by_date(history):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    grouped = {"Today": [], "Yesterday": [], "Older": {}}

    for item in history:
        try:
            dt = datetime.fromisoformat(item["timestamp"]).date()
        except ValueError:
            try:
                dt = datetime.strptime(item["timestamp"], "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                dt = today

        if dt == today:
            grouped["Today"].append(item)
        elif dt == yesterday:
            grouped["Yesterday"].append(item)
        else:
            grouped["Older"].setdefault(dt.strftime("%B %d, %Y"), []).append(item)

    return grouped

def login_register_form():
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🤖 Smart Document Assistant")
        st.markdown("---")

        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

        with tab1:
            with st.form("login_form"):
                st.subheader("Welcome Back!")
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    login_button = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")

                if login_button:
                    if not username or not password:
                        st.error("⚠️ Please enter both username and password")
                    else:
                        with st.spinner("Signing you in..."):
                            success, message = login_user(username, password)
                            if success:
                                st.success("✅ " + message)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ " + message)

        with tab2:
            with st.form("register_form"):
                st.subheader("Join Us Today!")
                username = st.text_input("👤 Choose Username", placeholder="Enter a unique username")
                email = st.text_input("📧 Email Address", placeholder="Enter your email")
                password = st.text_input("🔒 Create Password", type="password", placeholder="Create a strong password")
                confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    register_button = st.form_submit_button("🎯 Create Account", use_container_width=True, type="primary")

                if register_button:
                    if not username or not email or not password or not confirm_password:
                        st.error("⚠️ Please fill all fields")
                    elif password != confirm_password:
                        st.error("❌ Passwords don't match")
                    else:
                        with st.spinner("Creating your account..."):
                            success, message = register_user(username, email, password)
                            if success:
                                st.success("✅ " + message)
                            else:
                                st.error("❌ " + message)

def chat_interface():
    # Load chat history if not loaded
    if not st.session_state.chat_history:
        success, message = get_chat_history()
        if not success:
            st.error(f"Failed to load history: {message}")

    # Group chat history
    chat_grouped = group_history_by_date(st.session_state.chat_history)

    # Header with user info and controls
    header_col1, header_col2, header_col3 = st.columns([2, 2, 1])
    
    with header_col1:
        st.title(f"👋 Hello, {st.session_state.current_user['username']}!")
    
    with header_col2:
        # Toggle documents panel
        if st.button("📄 Toggle Documents" if not st.session_state.show_documents else "💬 Focus Chat", 
                    type="secondary", use_container_width=True):
            st.session_state.show_documents = not st.session_state.show_documents
            st.rerun()
    
    with header_col3:
        if st.button("🚪 Logout", type="primary", use_container_width=True):
            clear_token()
            st.session_state.token = None
            st.session_state.current_user = None
            st.session_state.chat_history = []
            st.session_state.user_documents = []
            st.session_state.show_documents = False
            st.session_state.current_chat = []
            st.rerun()

    st.divider()

    # Main layout
    if st.session_state.show_documents:
        left_col, main_col, right_col = st.columns([1, 2, 1])
    else:
        left_col, main_col = st.columns([1, 3])

    # Left sidebar - Chat History
    with left_col:
        st.subheader("📚 Chat History")
        
        # New Chat button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            st.session_state.current_chat = []
            st.session_state.selected_date = "Current"
            st.rerun()
        
        st.divider()
        
        # History navigation
        for label in ["Today", "Yesterday"]:
            count = len(chat_grouped[label])
            if count > 0:
                if st.button(f"{label} ({count})", key=f"nav_{label}", use_container_width=True,
                           type="primary" if st.session_state.selected_date == label else "secondary"):
                    st.session_state.selected_date = label
                    st.session_state.current_chat = chat_grouped[label]
                    st.rerun()

        # Older chats
        if chat_grouped["Older"]:
            st.markdown("**📅 Older Chats**")
            for older_date in sorted(chat_grouped["Older"].keys(), reverse=True):
                count = len(chat_grouped["Older"][older_date])
                if st.button(f"{older_date} ({count})", key=f"nav_{older_date}", 
                           use_container_width=True,
                           type="primary" if st.session_state.selected_date == older_date else "secondary"):
                    st.session_state.selected_date = older_date
                    st.session_state.current_chat = chat_grouped["Older"][older_date]
                    st.rerun()

    # Main chat area
    with main_col:
        # Chat header
        if st.session_state.selected_date == "Current":
            st.subheader("💭 New Conversation")
        else:
            st.subheader(f"💬 {st.session_state.selected_date}")
        
        # Chat messages container with fixed height
        chat_container = st.container(height=400)
        
        with chat_container:
            if st.session_state.current_chat:
                for i, chat in enumerate(st.session_state.current_chat):
                    # User message
                    with st.chat_message("user"):
                        st.write(chat["user_query"])
                    
                    # Assistant message
                    with st.chat_message("assistant"):
                        st.write(chat["bot_response"])
                        
                        # Sources
                        if chat.get("sources"):
                            with st.expander("📖 Sources", expanded=False):
                                for j, source in enumerate(chat["sources"], 1):
                                    st.markdown(f"**{j}.** {source}")
            else:
                st.info("🌟 Start a new conversation by typing your question below!")

        # Fixed input area at bottom
        st.divider()
        
        # Chat input form
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                user_input = st.text_input(
                    "Message", 
                    placeholder="Ask me anything about your documents...",
                    label_visibility="collapsed"
                )
            
            with col2:
                send_button = st.form_submit_button("🚀 Send", use_container_width=True, type="primary")
        
        # Handle message sending
        if send_button and user_input.strip():
            # Switch to current chat if not already
            if st.session_state.selected_date != "Current":
                st.session_state.selected_date = "Current"
                st.session_state.current_chat = []
            
            # Add user message immediately
            user_message = {
                "timestamp": datetime.now().isoformat(),
                "user_query": user_input,
                "bot_response": "Thinking...",
                "sources": []
            }
            st.session_state.current_chat.append(user_message)
            
            # Send query
            with st.spinner("🤔 Processing your question..."):
                success, result = send_query(user_input)
                if success:
                    # Update the last message
                    st.session_state.current_chat[-1]["bot_response"] = result["answer"]
                    st.session_state.current_chat[-1]["sources"] = result["sources"]
                else:
                    st.session_state.current_chat[-1]["bot_response"] = f"❌ Error: {result}"
            
            st.rerun()

    # Right panel - Documents (if shown)
    if st.session_state.show_documents:
        with right_col:
            st.subheader("📁 Document Manager")
            
            # Upload section
            with st.expander("📤 Upload New Document", expanded=True):
                uploaded_file = st.file_uploader(
                    "Choose a file", 
                    type=["pdf", "txt", "csv"],
                    help="Supported formats: PDF, TXT, CSV (Max 200MB)"
                )
                
                if uploaded_file:
                    if st.button("⬆️ Upload", type="primary", use_container_width=True):
                        with st.spinner("📊 Processing document..."):
                            success, message = upload_file(uploaded_file)
                            if success:
                                st.success("✅ " + message)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ " + message)
            
            # Documents list
            st.divider()
            st.markdown("**📚 Your Documents**")
            
            if not st.session_state.user_documents:
                get_user_documents()
            
            if st.session_state.user_documents:
                unique_docs = sorted({doc['source'] for doc in st.session_state.user_documents})
                
                for doc in unique_docs:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # Clean document name display
                        display_name = doc.split("/")[-1] if "/" in doc else doc
                        st.markdown(f"📄 **{display_name}**")
                    with col2:
                        if st.button("🗑️", key=f"del_{doc}", help=f"Delete {display_name}", 
                                   type="secondary"):
                            with st.spinner("Deleting..."):
                                success, message = delete_document(doc)
                                if success:
                                    st.success("✅ Deleted!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ " + message)
                    st.divider()
            else:
                st.info("📭 No documents uploaded yet. Upload your first document to get started!")

def main():
    st.set_page_config(
        page_title="Smart Document Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Hide Streamlit branding
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    if st.session_state.token is None or st.session_state.current_user is None:
        login_register_form()
    else:
        chat_interface()

if __name__ == "__main__":
    main()