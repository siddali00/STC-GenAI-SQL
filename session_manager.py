import streamlit as st
import uuid
from datetime import datetime
from database import (
    SessionLocal, save_chat_session, load_chat_session, 
    load_all_chat_sessions, delete_chat_session
)

def get_or_create_session_id():
    """Get existing session ID from browser session or create a new one"""
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = str(uuid.uuid4())
    return st.session_state.chat_session_id

def initialize_chat_system():
    """Initialize the chat system with database-based memory"""
    # Get current mode for module-specific chats
    current_mode = st.session_state.get('current_mode', 'SQL Query Assistant')
    
    # Get or create session ID
    session_id = get_or_create_session_id()
    
    if "current_messages" not in st.session_state:
        st.session_state.current_messages = []
    
    # Load existing session from database if it exists
    if "session_loaded" not in st.session_state:
        db = SessionLocal()
        try:
            session_data = load_chat_session(db, session_id)
            if session_data and session_data['module'] == current_mode:
                st.session_state.current_messages = session_data['messages']
                st.session_state.session_title = session_data['title']
            st.session_state.session_loaded = True
        finally:
            db.close()

def create_new_chat_session():
    """Create a new chat session"""
    # Save current session if it has messages
    if st.session_state.get('current_messages'):
        save_current_session()
    
    # Create new session
    st.session_state.chat_session_id = str(uuid.uuid4())
    st.session_state.current_messages = []
    st.session_state.session_loaded = False

def save_current_session():
    """Save the current chat session to database"""
    if not st.session_state.get('current_messages'):
        return
    
    session_id = get_or_create_session_id()
    current_mode = st.session_state.get('current_mode', 'SQL Query Assistant')
    
    # Create a title from the first user message (truncated)
    first_user_msg = next((msg for msg in st.session_state.current_messages if msg["role"] == "user"), None)
    if first_user_msg:
        title = first_user_msg["content"][:40] + "..." if len(first_user_msg["content"]) > 40 else first_user_msg["content"]
    else:
        title = f"Chat {datetime.now().strftime('%H:%M')}"
    
    # Save to database
    db = SessionLocal()
    try:
        success = save_chat_session(
            db=db,
            session_id=session_id,
            title=title,
            module=current_mode,
            messages=st.session_state.current_messages
        )
        if success:
            st.session_state.session_title = title
    finally:
        db.close()

def load_session(session_id: str):
    """Load a specific chat session"""
    # Save current session first
    save_current_session()
    
    # Load the selected session
    db = SessionLocal()
    try:
        session_data = load_chat_session(db, session_id)
        if session_data:
            st.session_state.chat_session_id = session_id
            st.session_state.current_messages = session_data['messages']
            st.session_state.session_title = session_data['title']
            # Force mode switch if needed
            if session_data['module'] != st.session_state.get('current_mode'):
                st.session_state.current_mode = session_data['module']
        else:
            st.error("Session not found")
    finally:
        db.close()

def delete_session(session_id: str):
    """Delete a chat session"""
    db = SessionLocal()
    try:
        success = delete_chat_session(db, session_id)
        if success:
            # If we're deleting the current session, create a new one
            if session_id == get_or_create_session_id():
                create_new_chat_session()
            return True
        return False
    finally:
        db.close()

def load_all_sessions(module: str = None):
    """Load all chat sessions for display"""
    db = SessionLocal()
    try:
        return load_all_chat_sessions(db, module)
    finally:
        db.close()

def add_message(role: str, content: str, metadata: dict = None):
    """Add a message to the current chat session"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(),
        "id": str(uuid.uuid4())
    }
    if metadata:
        message.update(metadata)
    
    st.session_state.current_messages.append(message)
    
    # Auto-save after each message
    save_current_session()

def get_session_memory():
    """Get the conversation history for the current session - useful for AI context"""
    messages = st.session_state.get('current_messages', [])
    
    # Format messages for AI context
    conversation_history = []
    for msg in messages[-10:]:  # Last 10 messages for context
        conversation_history.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    return conversation_history 