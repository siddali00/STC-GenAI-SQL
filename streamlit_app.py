import streamlit as st
import os
import re
import pandas as pd
from datetime import datetime
import cohere
from sqlalchemy import text
from database import SessionLocal
import json
import uuid
import pickle
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="STC Query Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global font styling */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        width: 220px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-right: none;
    }
    
    .css-1d391kg .css-1v0mbdj {
        padding: 1rem;
    }
    
    /* Sidebar title styling */
    .css-1d391kg h1 {
        color: white;
        font-weight: 600;
        margin-bottom: 1.5rem;
        text-align: center;
        font-size: 1.5rem;
    }
    
    /* Sidebar buttons */
    .css-1d391kg .stButton > button {
        background: rgba(255, 255, 255, 0.15);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .css-1d391kg .stButton > button:hover {
        background: rgba(255, 255, 255, 0.25);
        transform: translateY(-1px);
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.15);
        border-color: rgba(255, 255, 255, 0.4);
    }
    
    /* Primary buttons in sidebar */
    .css-1d391kg .stButton > button[kind="primary"] {
        background: linear-gradient(45deg, #ff6b6b, #ee5a52);
        border: none;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(238, 90, 82, 0.3);
    }
    
    .css-1d391kg .stButton > button[kind="primary"]:hover {
        background: linear-gradient(45deg, #ff5252, #d32f2f);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(238, 90, 82, 0.4);
    }
    
    /* Sidebar captions */
    .css-1d391kg .css-nahz7x {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.8rem;
    }
    
    /* Sidebar divider */
    .css-1d391kg hr {
        border-color: rgba(255, 255, 255, 0.3);
        margin: 1rem 0;
    }
    
    /* Main content area */
    .css-18e3th9 {
        padding: 2rem;
    }
    
    /* Title styling */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        margin-bottom: 2rem;
        text-align: center;
        font-size: 2.5rem;
    }
    
    /* Chat messages styling */
    .stChatMessage {
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .stChatMessage[data-testid="chat-message-user"] {
        background: linear-gradient(135deg, #4a6cf7 0%, #3b5bd9 100%);
        color: white;
        margin-left: 2rem;
        border: none;
    }
    
    .stChatMessage[data-testid="chat-message-user"] .stMarkdown,
    .stChatMessage[data-testid="chat-message-user"] .stMarkdown p {
        color: white !important;
    }
    
    .stChatMessage[data-testid="chat-message-assistant"] {
        background: rgba(248, 249, 250, 0.95);
        margin-right: 2rem;
        border-left: 4px solid #4a6cf7;
    }
    
    .stChatMessage[data-testid="chat-message-assistant"] .stMarkdown,
    .stChatMessage[data-testid="chat-message-assistant"] .stMarkdown p {
        color: #1a1f36 !important;
    }
    
    /* Chat input styling */
    .stChatInput > div > div > textarea {
        min-height: 60px !important;
        font-size: 16px !important;
        border-radius: 15px !important;
        border: 2px solid #e1e5e9 !important;
        padding: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    
    .stChatInput > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 0.75rem;
        font-weight: 500;
        border: 1px solid #dee2e6;
    }
    
    .streamlit-expanderContent {
        background: #f8f9fa;
        border-radius: 0 0 10px 10px;
        border: 1px solid #dee2e6;
        border-top: none;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background: #f8f9fa;
        border-radius: 10px 10px 0 0;
        padding: 0 1.5rem;
        font-weight: 500;
        border: 1px solid #dee2e6;
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        color: #667eea;
        border-color: #667eea;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #e1e5e9;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
        padding: 0.5rem 2rem;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(45deg, #5a67d8, #6b46c1);
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: #667eea transparent #667eea transparent;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #b6d7a8;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .stError {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #f1aeb5;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Code block styling */
    .stCodeBlock {
        border-radius: 10px;
        border: 1px solid #e1e5e9;
    }
    
    /* Processing text animation */
    .processing-text {
        background: linear-gradient(45deg, #667eea, #764ba2, #667eea);
        background-size: 200% 200%;
        animation: gradient 2s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 500;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Module selector styling */
    .css-1d391kg .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        color: white;
        backdrop-filter: blur(10px);
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    
    .css-1d391kg .stSelectbox > div > div:hover {
        background: rgba(255, 255, 255, 0.25);
        border-color: rgba(255, 255, 255, 0.4);
    }
    
    .css-1d391kg .stSelectbox > div > div > div {
        color: white;
    }
    
    /* Sidebar status indicator */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4ade80;
        animation: pulse 2s infinite;
        margin-right: 0.5rem;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border: 1px solid #f0f2f6;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }
    
    .metric-label {
        color: #6c757d;
        font-weight: 500;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────
# MODULE SWITCHING
# ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem; padding: 0.8rem; background: rgba(255, 255, 255, 0.1); border-radius: 12px; backdrop-filter: blur(10px);">
        <h2 style="color: white; margin: 0; font-size: 1.2rem;">🎯 Mode</h2>
    </div>
    """, unsafe_allow_html=True)
    
    mode = st.selectbox(
        "",
        ["💬 Chat Assistant", "🔴 Incident Analyzer"],
        label_visibility="collapsed"
    )
    
    # Remove emoji from mode for logic
    if "Chat Assistant" in mode:
        mode = "SQL Query Assistant"
    else:
        mode = "Data Incident Explainer"
    
    st.markdown("---")

# File path for persistent storage
CHAT_STORAGE_FILE = Path("chat_sessions.pkl")

# Initialize Cohere client
@st.cache_resource
def init_cohere_client():
    """Initialize Cohere client with caching"""
    with st.spinner("🔄 Initializing AI assistant..."):
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            st.error("❌ **COHERE_API_KEY environment variable not set!**")
            st.markdown("""
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 10px; padding: 1rem; margin: 1rem 0;">
                <p><strong>🔧 Setup Required:</strong></p>
                <p>Please set your Cohere API key as an environment variable:</p>
                <code>export COHERE_API_KEY=your_api_key_here</code>
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        
        # Test database connection
        try:
            test_session = SessionLocal()
            test_session.execute(text("SELECT 1"))
            test_session.close()
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            st.error(f"❌ Database connection failed: {str(e)}")
        
        return cohere.ClientV2(api_key=api_key)

co = init_cohere_client()

# Database schema information (hidden from user)
SCHEMA_INFO = """
Available Tables:
- sales(date DATE, region TEXT, product TEXT, units_sold INTEGER, revenue NUMERIC)
- churn(month DATE, segment TEXT, churned_customers INTEGER)
"""

def load_chat_sessions_from_file():
    """Load chat sessions from file"""
    try:
        if CHAT_STORAGE_FILE.exists():
            with open(CHAT_STORAGE_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        st.error(f"Error loading chat sessions: {e}")
    return {}

def save_chat_sessions_to_file(chat_sessions):
    """Save chat sessions to file"""
    try:
        with open(CHAT_STORAGE_FILE, 'wb') as f:
            pickle.dump(chat_sessions, f)
    except Exception as e:
        st.error(f"Error saving chat sessions: {e}")

def initialize_chat_system():
    """Initialize the chat system with persistent storage"""
    # Get current mode for module-specific chats
    current_mode = st.session_state.get('current_mode', 'SQL Query Assistant')
    
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = str(uuid.uuid4())
    
    if "chat_sessions" not in st.session_state:
        # Load from file
        all_chats = load_chat_sessions_from_file()
        st.session_state.chat_sessions = all_chats
    
    # Get module-specific chats
    module_key = f"{current_mode}_chats"
    if module_key not in st.session_state.chat_sessions:
        st.session_state.chat_sessions[module_key] = {}
    
    if "current_messages" not in st.session_state:
        # If we have a current chat ID, try to load its messages from current module
        module_chats = st.session_state.chat_sessions[module_key]
        if st.session_state.current_chat_id in module_chats:
            st.session_state.current_messages = module_chats[st.session_state.current_chat_id]["messages"].copy()
        else:
            st.session_state.current_messages = []

def create_new_chat():
    """Create a new chat session"""
    # Save current chat if it has messages
    if st.session_state.current_messages:
        save_current_chat()
    
    # Create new chat
    new_chat_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_chat_id
    st.session_state.current_messages = []

def save_current_chat():
    """Save the current chat session"""
    if st.session_state.current_messages:
        # Get current mode for module-specific storage
        current_mode = st.session_state.get('current_mode', 'SQL Query Assistant')
        module_key = f"{current_mode}_chats"
        
        # Ensure module storage exists
        if module_key not in st.session_state.chat_sessions:
            st.session_state.chat_sessions[module_key] = {}
        
        # Create a title from the first user message (truncated)
        first_user_msg = next((msg for msg in st.session_state.current_messages if msg["role"] == "user"), None)
        if first_user_msg:
            title = first_user_msg["content"][:40] + "..." if len(first_user_msg["content"]) > 40 else first_user_msg["content"]
        else:
            title = f"Chat {datetime.now().strftime('%H:%M')}"
        
        st.session_state.chat_sessions[module_key][st.session_state.current_chat_id] = {
            "title": title,
            "messages": st.session_state.current_messages.copy(),
            "timestamp": datetime.now(),
            "module": current_mode
        }
        
        # Save to file
        save_chat_sessions_to_file(st.session_state.chat_sessions)

def load_chat(chat_id):
    """Load a specific chat session"""
    # Save current chat first
    save_current_chat()
    
    # Get current mode for module-specific loading
    current_mode = st.session_state.get('current_mode', 'SQL Query Assistant')
    module_key = f"{current_mode}_chats"
    
    # Load selected chat from current module
    if module_key in st.session_state.chat_sessions and chat_id in st.session_state.chat_sessions[module_key]:
        st.session_state.current_chat_id = chat_id
        st.session_state.current_messages = st.session_state.chat_sessions[module_key][chat_id]["messages"].copy()
    else:
        st.session_state.current_chat_id = chat_id
        st.session_state.current_messages = []

def delete_chat(chat_id):
    """Delete a chat session"""
    # Get current mode for module-specific deletion
    current_mode = st.session_state.get('current_mode', 'SQL Query Assistant')
    module_key = f"{current_mode}_chats"
    
    if module_key in st.session_state.chat_sessions and chat_id in st.session_state.chat_sessions[module_key]:
        del st.session_state.chat_sessions[module_key][chat_id]
        
        # Save to file
        save_chat_sessions_to_file(st.session_state.chat_sessions)
        
        # If we're deleting the current chat, create a new one
        if st.session_state.current_chat_id == chat_id:
            create_new_chat()

def classify_user_intent(user_question: str) -> str:
    """Classify user intent to determine if it's data-related, greeting, or irrelevant"""
    try:
        system_prompt = (
            """You are a classifier for user intents in a data analysis chat system. 

            Classify the user's message into one of these categories:
            - 'data_query': Questions about data, analytics, sales, revenue, customers, churn, products, regions, etc.
            - 'greeting': Greetings, hellos, how are you, etc.
            - 'irrelevant': Questions not related to data analysis (weather, sports, personal questions, etc.)
            
            Return ONLY the category name, nothing else."""
        )
        
        resp = co.chat(
            model="command-r-08-2024",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ]
        )
        
        intent = resp.message.content[0].text.strip().lower()
        return intent if intent in ['data_query', 'greeting', 'irrelevant'] else 'data_query'
        
    except Exception as e:
        # Default to data_query if classification fails
        return 'data_query'

def generate_contextual_response(user_question: str, intent: str) -> str:
    """Generate a contextual response based on user intent using Cohere"""
    try:
        if intent == 'data_query':
            system_prompt = (
                """You are a helpful business data assistant. The user is asking about business data analysis, but you don't have access to their specific data right now. Explain that you can help them analyze their sales, customer, and churn data, and ask them to be more specific about what they'd like to know. Be friendly and professional."""
            )
        elif intent == 'greeting':
            system_prompt = (
                """You are a friendly business data assistant. The user is greeting you. Respond naturally and let them know you can help them analyze their business data including sales, customers, and churn metrics. Be conversational and welcoming."""
            )
        else:  # irrelevant
            system_prompt = (
                "You are a business data assistant. The user is asking about something unrelated to business data analysis. Politely acknowledge their question but redirect them to ask about business data, sales, customers, or analytics instead. Be friendly but stay focused on your role."
            )
        
        resp = co.chat(
            model="command-r-08-2024",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ]
        )
        return resp.message.content[0].text.strip()
        
    except Exception as e:
        return "I'm here to help you analyze your business data. What would you like to know about your sales, customers, or business metrics?"

def execute_sql_query(sql: str) -> tuple[pd.DataFrame, str, bool]:
    """Execute SQL query and return results as DataFrame, status message, and success flag"""
    try:
        # Clean SQL (remove markdown formatting if present)
        sql_match = re.search(r'```sql\s*(.*?)\s*```', sql, re.DOTALL)
        clean_sql = sql_match.group(1).strip() if sql_match else sql.strip()
        
        session = SessionLocal()
        try:
            result = session.execute(text(clean_sql))
            rows = result.fetchall()
            cols = result.keys()
            
            if not rows:
                return pd.DataFrame(), "🔍 No rows returned from the query.", True
            
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=cols)
            return df, f"✅ Query executed successfully. Found {len(df)} rows.", True
            
        finally:
            session.close()
            
    except Exception as e:
        return pd.DataFrame(), f"❌ Error executing SQL: {str(e)}", False

def generate_sql_query(user_question: str) -> str:
    """Generate SQL query using Cohere API"""
    try:
        system_prompt = (
            "You are a SQL assistant. Given a natural-language question and a database schema, generate a valid PostgreSQL query. **Use case-insensitive matching (e.g. `ILIKE`) when filtering text columns like `region` or `segment.** Return ONLY the SQL query, no explanation or markdown formatting."
        )
        
        user_prompt = f"{SCHEMA_INFO}\nQuestion: {user_question}"
        
        resp = co.chat(
            model="command-r-08-2024",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        sql = resp.message.content[0].text.strip()
        # Remove any markdown formatting
        sql = re.sub(r'```sql\n?|```\n?', '', sql).strip()
        return sql
        
    except Exception as e:
        return f"Error generating SQL: {str(e)}"

def generate_natural_language_response(user_question: str, sql_query: str, df: pd.DataFrame, execution_status: str, success: bool) -> str:
    """Generate a natural language response based on the query results"""
    try:
        if not success:
            return f"I encountered an error while analyzing your data: {execution_status}. Could you try rephrasing your question?"
        
        if df.empty:
            return "I searched your data but didn't find any results matching your criteria. You might want to try a different time period or criteria."
        
        # Convert DataFrame to a readable format for the AI
        data_summary = f"Query returned {len(df)} rows with columns: {', '.join(df.columns)}\n"
        
        # Include sample data (first few rows)
        if len(df) > 0:
            data_summary += f"Sample data:\n{df.head(5).to_string(index=False)}"
        
        system_prompt = (
            "You are a friendly business data analyst. Based on a user's question and the query results,provide a conversational summary of the findings. Be helpful, insightful, and highlight key business insights. Keep it natural and easy to understand. Keep your answer short and to the point. Do not go into depths explaining the data results. Keep it simple and concise."
        )
        
        user_prompt = f"""
User Question: {user_question}
Results Summary: {data_summary}

Please provide a natural, conversational response summarizing these findings and any business insights.
"""
        
        resp = co.chat(
            model="command-r-08-2024",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return resp.message.content[0].text.strip()
        
    except Exception as e:
        return f"I found some data for your question ({len(df)} records), but had trouble summarizing it. Could you try asking in a different way?"

def add_message(role: str, content: str, metadata: dict = None):
    """Add a message to the current chat"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(),
        "id": str(uuid.uuid4())
    }
    if metadata:
        message.update(metadata)
    st.session_state.current_messages.append(message)

def process_user_question(user_question: str):
    """Process user question based on intent"""
    
    # Add user message
    add_message("user", user_question)
    
    # Classify user intent
    intent = classify_user_intent(user_question)
    
    if intent == 'greeting' or intent == 'irrelevant':
        # Let Cohere handle greetings and irrelevant questions naturally
        response = generate_contextual_response(user_question, intent)
        add_message("assistant", response)
        return
    
    # Handle data query
    else:
        # Generate SQL
        sql_query = generate_sql_query(user_question)
        
        if sql_query.startswith("Error"):
            # Use Cohere to generate a natural response for SQL generation errors
            error_response = generate_contextual_response(
                f"I had trouble generating a query for: {user_question}", 'data_query'
            )
            add_message("assistant", error_response)
            return
        
        # Execute SQL
        df, execution_status, success = execute_sql_query(sql_query)
        
        # Generate natural language response
        nl_response = generate_natural_language_response(
            user_question, sql_query, df, execution_status, success
        )
        
        # Add assistant response with metadata
        add_message("assistant", nl_response, {
            "sql_query": sql_query,
            "data": df,
            "execution_status": execution_status,
            "success": success
        })

# ────────────────────────────────────────────────────────────────
# 5) INCIDENT EXPLAINER FUNCTIONS (only this section changes)
# ────────────────────────────────────────────────────────────────

def fetch_failure(log_id: int):
    session = SessionLocal()
    try:
        # Add debugging - check what's actually in the table
        print(f"Fetching data for log_id: {log_id}")
        
        # First, let's see what columns exist
        columns_result = session.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'job_logs'")
        ).fetchall()
        print(f"Available columns: {[row[0] for row in columns_result]}")
        
        # Check if the record exists at all
        exists_check = session.execute(
            text("SELECT COUNT(*) FROM job_logs WHERE log_id = :id"),
            {"id": log_id}
        ).fetchone()
        print(f"Records found for log_id {log_id}: {exists_check[0]}")
        
        # Get the actual record
        r = session.execute(
            text("SELECT * FROM job_logs WHERE log_id = :id"),
            {"id": log_id}
        ).fetchone()
        
        if r:
            print(f"Raw result: {dict(r._mapping)}")
            
            # Try to get the specific columns you need
            result = session.execute(
                text("SELECT log_id, job_name, run_timestamp, message FROM job_logs WHERE log_id=:id"),
                {"id": log_id}
            ).fetchone()
            
            if result:
                data = dict(result._mapping)
                data["run_timestamp"] = data["run_timestamp"].isoformat()
                print(f"Processed result: {data}")
                return data
            else:
                return {"error": "specific columns not found"}
        else:
            return {"error": "record not found"}
            
    except Exception as e:
        print(f"Error in fetch_failure: {str(e)}")
        return {"error": f"database error: {str(e)}"}
    finally:
        session.close()

def lookup_kb(error_message: str):
    session = SessionLocal()
    try:
        r = session.execute(
            text("SELECT root_cause_en, resolution_en, root_cause_ar, resolution_ar "
                 "FROM incident_kb WHERE :msg ILIKE error_pattern LIMIT 1"),
            {"msg": error_message}
        ).fetchone()
    finally:
        session.close()
    if not r:
        return {
            "root_cause_en":"Unknown cause",
            "resolution_en":"Manual investigation required",
            "root_cause_ar":"سبب غير معروف",
            "resolution_ar":"مطلوب تحقيق يدوي"
        }
    return dict(r._mapping)

# Function definitions for tools
functions = [
    {
        "name": "fetch_failure",
        "description": "Retrieve detailed job failure information by log ID including job name, timestamp, and error message",
        "parameters": {
            "type": "object",
            "properties": {
                "log_id": {
                    "type": "integer",
                    "description": "The unique identifier for the job log entry"
                }
            },
            "required": ["log_id"]
        }
    },
    {
        "name": "lookup_kb",
        "description": "Search knowledge base for root cause analysis and resolution steps based on error message pattern",
        "parameters": {
            "type": "object",
            "properties": {
                "error_message": {
                    "type": "string",
                    "description": "The error message to search for in the knowledge base"
                }
            },
            "required": ["error_message"]
        }
    }
]

func_map = {
    "fetch_failure": fetch_failure,
    "lookup_kb": lookup_kb
}

tool_defs = [
    {
        "type": "function",
        "function": {
            "name": f["name"],
            "description": f["description"],
            "parameters": f["parameters"]
        }
    }
    for f in functions
]

def explain_incident_agent(log_id: int) -> str:
    """
    Analyze and explain an incident by fetching log details and providing 
    root cause analysis with resolution steps.
    """
    print(f"DEBUG: Starting analysis for log_id: {log_id}")
    
    user_msg = (
        f"Please analyze incident log ID {log_id}. "
        f"First, fetch the failure details using the log ID. "
        f"Then, use the error message to look up root cause and resolution information. "
        f"Provide a comprehensive explanation including:\n"
        f"1. Job details (name, timestamp)\n"
        f"2. Error message analysis\n"
        f"3. Root cause explanation\n"
        f"4. Detailed resolution steps\n"
        f"5. Preventive measures if applicable"
    )
    
    try:
        print(f"DEBUG: Making first API call...")
        # First API call with tools
        first_response = co.chat(
            model="command-r-08-2024",
            messages=[{"role": "user", "content": user_msg}],
            tools=tool_defs,
            temperature=0.1
        )
        
        print(f"DEBUG: First response received: {hasattr(first_response, 'message')}")
        
        if not hasattr(first_response, 'message') or first_response.message is None:
            return "Error: No response received from the model"
        
        msg = first_response.message
        tool_calls = getattr(msg, 'tool_calls', None)
        
        print(f"DEBUG: Tool calls found: {len(tool_calls) if tool_calls else 0}")
        
        if not tool_calls or len(tool_calls) == 0:
            # No tool calls made - return direct response or error
            content = getattr(msg, 'content', '')
            return content if content else f"Model didn't make required tool calls for log_id {log_id}"
        
        print(f"Processing {len(tool_calls)} tool calls")
        
        # Execute all tool calls and collect results
        tool_results = []
        executed_tools_info = []  # For creating summary
        
        for call in tool_calls:
            try:
                args = json.loads(call.function.arguments)
                result = func_map[call.function.name](**args)
                
                tool_results.append({
                    "role": "tool", 
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str)
                })
                
                # Store for summary
                executed_tools_info.append({
                    "function": call.function.name,
                    "args": args,
                    "result": result
                })
                
            except Exception as e:
                error_result = {"error": str(e)}
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": call.id, 
                    "content": json.dumps(error_result)
                })
                executed_tools_info.append({
                    "function": call.function.name,
                    "args": args if 'args' in locals() else {},
                    "result": error_result
                })

        # Create a comprehensive summary of all tool results
        tools_summary = "Tool Execution Results:\n\n"
        for i, tool_info in enumerate(executed_tools_info, 1):
            tools_summary += f"{i}. Function: {tool_info['function']}\n"
            tools_summary += f"   Arguments: {tool_info['args']}\n"
            tools_summary += f"   Result: {json.dumps(tool_info['result'], indent=2, default=str)}\n\n"

        # Build complete conversation history
        conversation = [
            {"role": "user", "content": user_msg},
            {
                "role": "assistant",
                "content": getattr(msg, 'content', '') or '',
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function", 
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments
                        }
                    } for call in tool_calls
                ]
            }
        ]
        
        # Add all tool results
        conversation.extend(tool_results)
        
        # Add analysis request with tool results summary
        analysis_prompt = (
            f"Based on the tool execution results above, please provide a comprehensive incident analysis report for log ID {log_id}. "
            f"Here's a summary of what was retrieved:\n\n{tools_summary}"
            f"Please analyze this information and provide:\n"
            f"1. Complete job failure details\n"
            f"2. Root cause analysis\n" 
            f"3. Step-by-step resolution instructions\n"
            f"4. Preventive measures\n"
            f"5. Any additional insights\n\n"
            f"Do not make any additional tool calls - just provide a detailed analysis based on the data above."
        )
        
        conversation.append({
            "role": "user", 
            "content": analysis_prompt
        })
        
        # Second API call WITHOUT tools
        second_response = co.chat(
            model="command-r-08-2024",
            messages=conversation,
            temperature=0.1
        )
        
        if not hasattr(second_response, 'message') or second_response.message is None:
            return f"Error: No second response received. Tool results were: {tools_summary}"
        
        final_msg = second_response.message
        
        # Check if it inappropriately made more tool calls
        if hasattr(final_msg, 'tool_calls') and final_msg.tool_calls:
            return (f"Error: Model made unexpected tool calls in second response. "
                   f"Tool summary: {tools_summary}")
        
        # Extract and return content
        content = getattr(final_msg, 'content', None)
        if not content:
            return f"Error: No content in final response. Tool results: {tools_summary}"
        
        # Handle different content formats
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if hasattr(block, 'text'):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and 'text' in block:
                    text_parts.append(block['text'])
                elif isinstance(block, str):
                    text_parts.append(block)
            
            final_content = '\n'.join(text_parts) if text_parts else None
        elif isinstance(content, str):
            final_content = content
        else:
            final_content = str(content)
        
        
        if not final_content or final_content.strip() == '':
            return f"Error: Empty final response. Tool results were: {tools_summary}"
        
        print(f"DEBUG: Final content length: {len(final_content)}")
        print(f"DEBUG: Final content preview: {final_content[:200]}...")
        return final_content
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"DEBUG: Exception occurred: {str(e)}")
        return f"Error in incident analysis: {str(e)}\n\nFull traceback:\n{error_trace}"

def render_sidebar():
    """Render the chat history sidebar"""
    with st.sidebar:
        # Get current mode for display
        current_mode = st.session_state.get('current_mode', 'SQL Query Assistant')
        mode_emoji = "💬" if "SQL" in current_mode else "🔴"
        mode_short = "SQL" if "SQL" in current_mode else "Incident"
        
        # Compact sidebar header with status
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h1 style="margin: 0; font-size: 1.4rem; color: white;">
                <span class="status-indicator"></span>{mode_emoji} {mode_short} Chats
            </h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact new chat button
        if st.button("➕ New", use_container_width=True, type="primary"):
            create_new_chat()
            st.rerun()
        
        st.markdown("---")
        
        # Display chat sessions with more compact styling
        if st.session_state.chat_sessions:
            # Get current mode for module-specific chat display
            current_mode = st.session_state.get('current_mode', 'SQL Query Assistant')
            module_key = f"{current_mode}_chats"
            
            # Get chats for current module only
            module_chats = st.session_state.chat_sessions.get(module_key, {})
            
            if module_chats:
                # Sort chats by timestamp (newest first)
                sorted_chats = sorted(
                    module_chats.items(),
                    key=lambda x: x[1]["timestamp"],
                    reverse=True
                )
                
                # Show only recent 5 chats for cleaner look
                for chat_id, chat_data in sorted_chats[:5]:
                    col1, col2 = st.columns([3.5, 0.5])
                    
                    with col1:
                        # Chat button with current chat highlighting
                        is_current = chat_id == st.session_state.current_chat_id
                        # Truncate title to fit better
                        title = chat_data['title'][:25] + "..." if len(chat_data['title']) > 25 else chat_data['title']
                        button_label = f"{'🟢' if is_current else '💭'} {title}"
                        
                        if st.button(
                            button_label,
                            key=f"chat_{chat_id}",
                            use_container_width=True,
                            type="primary" if is_current else "secondary"
                        ):
                            if chat_id != st.session_state.current_chat_id:
                                load_chat(chat_id)
                                st.rerun()
                    
                    with col2:
                        # Compact delete button
                        if st.button("🗑", key=f"delete_{chat_id}", help="Delete"):
                            delete_chat(chat_id)
                            st.rerun()
                    
                    # Compact timestamp
                    timestamp_str = chat_data["timestamp"].strftime("%m/%d")
                    st.markdown(f"<small style='color: rgba(255, 255, 255, 0.5); font-size: 0.7rem;'>{timestamp_str}</small>", unsafe_allow_html=True)
                    
                # Show more chats indicator if there are more than 5
                if len(sorted_chats) > 5:
                    st.markdown(f"<small style='color: rgba(255, 255, 255, 0.6); text-align: center; display: block;'>+{len(sorted_chats) - 5} more chats</small>", unsafe_allow_html=True)
            else:
                # Compact empty state for current module
                module_name = "SQL" if "SQL" in current_mode else "Incident"
                st.markdown(f"""
                <div style="text-align: center; color: rgba(255, 255, 255, 0.6); padding: 1rem 0;">
                    <p style="margin: 0;">No {module_name} chats yet</p>
                    <small>Start chatting!</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Compact empty state
            st.markdown("""
            <div style="text-align: center; color: rgba(255, 255, 255, 0.6); padding: 1rem 0;">
                <p style="margin: 0;">No chats yet</p>
                <small>Start chatting!</small>
            </div>
            """, unsafe_allow_html=True)

def render_footer():
    """Render a beautiful footer"""
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #6c757d;">
        <p style="margin: 0; font-size: 0.9rem;">
            🚀 <strong>STC Query Assistant</strong> | 
        </p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem;">
            Built using Streamlit & Cohere | 
            <a href="#" style="color: #667eea; text-decoration: none;">Documentation</a> | 
            <a href="#" style="color: #667eea; text-decoration: none;">Support</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Set current mode in session state for module-specific chats
    if 'current_mode' not in st.session_state:
        st.session_state.current_mode = mode
    elif st.session_state.current_mode != mode:
        # Mode changed - save current chat and switch context
        if st.session_state.get('current_messages'):
            save_current_chat()
        st.session_state.current_mode = mode
        # Start fresh for the new module
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.current_messages = []
    
    # Initialize chat system
    initialize_chat_system()
    
    # Render sidebar
    render_sidebar()
    
    if mode == "SQL Query Assistant":
        # Enhanced SQL Query Assistant UI
        st.markdown("""
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="margin: 0;">💬 STC Chat Assistant</h1>
            <p style="color: #6c757d; font-size: 1.2rem; margin-top: 0.5rem;">Ask questions about your business data in natural language</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Welcome cards when no messages
        if not st.session_state.current_messages:
            st.markdown("### 🚀 Get Started")
            
            # Sample questions in cards
            col1, col2, col3 = st.columns(3)
            
            sample_questions = [
                "How many units of Product A were sold overall?",
                "Which customer segments had the highest churn in january 2024?",
                "What were the sales numbers in Q4 2024 for north region?"
            ]
            
            for i, (col, question) in enumerate(zip([col1, col2, col3], sample_questions)):
                with col:
                    if st.button(f"💡 {question}", key=f"sample_{i}", use_container_width=True):
                        # Process the question (this will add both user and assistant messages)
                        try:
                            with st.spinner("🤔 Processing your question..."):
                                process_user_question(question)
                            
                            # Save and rerun to display the conversation
                            save_current_chat()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error processing question: {str(e)}")
                            # Add error message to chat
                            add_message("assistant", f"I encountered an error while processing your question: {str(e)}")
                            save_current_chat()
                            st.rerun()
            
            st.markdown("---")
            st.markdown("### 💡 **Tips for better results:**")
            st.markdown("""
            - Be specific about time periods and metrics
            - Ask about sales, revenue, customers, or churn data
            - Use natural language - no need for technical terms
            """)
        
        # Display current chat messages
        for message in st.session_state.current_messages:
            with st.chat_message(message["role"]):
                # Display the message content
                st.markdown(message["content"])
                
                # Show optional details for data queries
                if message["role"] == "assistant" and "sql_query" in message:
                    with st.expander("🔍 View Generated SQL", expanded=False):
                        st.markdown("""
                        <div style="background: #1e1e1e; 
                                    border-radius: 8px; 
                                    border: 1px solid #2d2d2d;
                                    margin-top: 0.5rem;">
                        """, unsafe_allow_html=True)
                        st.code(message["sql_query"], language="sql")
                        st.markdown("</div>", unsafe_allow_html=True)
        
        # Enhanced chat input
        if prompt := st.chat_input("💭 Ask me about your business data..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown('<p class="processing-text">🤔 Processing your question...</p>', unsafe_allow_html=True)
                process_user_question(prompt)
                placeholder.empty()
                latest = st.session_state.current_messages[-1]
                st.markdown(latest["content"])
                
                if "sql_query" in latest:
                    with st.expander("🔍 View Generated SQL", expanded=False):
                        st.markdown("""
                        <div style="background: #1e1e1e; 
                                    border-radius: 8px; 
                                    border: 1px solid #2d2d2d;
                                    margin-top: 0.5rem;">
                        """, unsafe_allow_html=True)
                        st.code(latest["sql_query"], language="sql")
                        st.markdown("</div>", unsafe_allow_html=True)
            
            save_current_chat()
            st.rerun()
    
    else:
        # Enhanced Data Incident Explainer UI
        st.markdown("""
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="margin: 0;">🔴 Data Pipeline Incident Explainer</h1>
            <p style="color: #6c757d; font-size: 1.2rem; margin-top: 0.5rem;">Analyze failed data pipeline runs and get resolution steps</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics dashboard
        col1, col2, col3 = st.columns(3)
        
        # Fetch failure statistics
        session = SessionLocal()
        total_failures = session.execute(
            text("SELECT COUNT(*) FROM job_logs WHERE status='FAILURE'")
        ).fetchone()[0]
        
        recent_failures = session.execute(
            text("SELECT COUNT(*) FROM job_logs WHERE status='FAILURE' AND run_timestamp >= NOW() - INTERVAL '24 hours'")
        ).fetchone()[0]
        
        unique_jobs = session.execute(
            text("SELECT COUNT(DISTINCT job_name) FROM job_logs WHERE status='FAILURE'")
        ).fetchone()[0]
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_failures}</div>
                <div class="metric-label">Total Failures</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{recent_failures}</div>
                <div class="metric-label">Last 24 Hours</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{unique_jobs}</div>
                <div class="metric-label">Affected Jobs</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Failure selection section
        st.markdown("### 📋 Select Failed Run")
        
        # Fetch recent failures with better formatting
        rows = session.execute(
            text("SELECT log_id, job_name, run_timestamp FROM job_logs WHERE status='FAILURE' ORDER BY run_timestamp DESC LIMIT 50")
        ).fetchall()
        session.close()
        
        if rows:
            options = [
                f"🔴 {r._mapping['log_id']} | {r._mapping['job_name']} @ {r._mapping['run_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
                for r in rows
            ]
            selected = st.selectbox(
                "Choose a failed pipeline run to analyze:",
                options,
                help="Select from the most recent 50 failures"
            )
            
            if st.button("🔍 Explain Incident", type="primary", use_container_width=True):
                log_id = int(selected.split("|")[0].strip().replace("🔴 ", ""))
                
                with st.spinner("🔄 Analyzing incident and generating report..."):
                    try:
                        explanation = explain_incident_agent(log_id)
                        st.success("✅ Analysis completed!")
                    except Exception as e:
                        st.error(f"❌ Error during analysis: {str(e)}")
                        explanation = f"Error occurred: {str(e)}"
                
                # Display the explanation
                st.markdown("### 📊 Incident Analysis Report")
                
                if explanation and explanation.strip():
                    # Display in a styled container
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                                padding: 1.5rem; 
                                border-radius: 12px; 
                                border-left: 4px solid #dc3545; 
                                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                                margin: 1rem 0;">
                    """, unsafe_allow_html=True)
                    
                    st.markdown(explanation)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Show character count for debugging
                    st.caption(f"Report length: {len(explanation)} characters")
                else:
                    st.error("❌ No report content was generated")
                    st.info(f"🔧 Debug info: explanation = '{explanation}' (type: {type(explanation)})")
                    
                    # Try to get some basic info manually
                    st.markdown("**Attempting manual data fetch:**")
                    try:
                        failure_data = fetch_failure(log_id)
                        st.json(failure_data)
                    except Exception as e:
                        st.error(f"Manual fetch failed: {str(e)}")
        else:
            st.info("ℹ️ No failed pipeline runs found in the database.")

    # Render footer
    render_footer()

if __name__ == "__main__":
    main()
