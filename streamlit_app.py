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
from pathlib import Path

# Import simplified session management
from session_manager import (
    initialize_chat_system, create_new_chat_session, 
    save_current_session, load_session, delete_session,
    load_all_sessions, add_message, get_session_memory,
    get_or_create_session_id
)

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
    
    /* RTL support for selectbox labels and content */
    .stSelectbox label {
        direction: rtl !important;
        text-align: right !important;
        width: 100% !important;
    }
    .stSelectbox > div > div {
        direction: rtl !important;
        text-align: right !important;
    }
    /* Additional styling for the selectbox container */
    .stSelectbox {
        direction: rtl !important;
    }
    /* Style for the selectbox options */
    .stSelectbox > div > div > div[role="listbox"] {
        direction: rtl !important;
        text-align: right !important;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────
# MODULE SWITCHING
# ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem; padding: 0.8rem; background: rgba(255, 255, 255, 0.1); border-radius: 12px; backdrop-filter: blur(10px);">
        <h2 style="color: white; margin: 0; font-size: 1.2rem;"> وضع 🎯</h2>
    </div>
    """, unsafe_allow_html=True)
    
    mode = st.selectbox(
        "",
        [" مساعد الدردشة 💬 ", " محلل الحوادث 🔴 "],
        label_visibility="collapsed"
    )
    
    # Fix mode detection logic
    if " مساعد الدردشة" in mode:
        mode = "SQL Query Assistant"
    else:
        mode = "Data Incident Explainer"
    
    st.markdown("---")

# File path for persistent storage (deprecated - now using database)
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

def classify_user_intent(user_question: str) -> str:
    """Classify user intent to determine if it's data-related, greeting, or irrelevant"""
    try:
        # Get conversation history for context
        conversation_history = get_session_memory()
        
        system_prompt = (
            """You are a classifier for user intents in a data analysis chat system. 

            Classify the user's message into one of these categories:
            - 'data_query': Questions about data, analytics, sales, revenue, customers, churn, products, regions, etc.
            - 'greeting': Greetings, hellos, how are you, etc.
            - 'irrelevant': Questions not related to data analysis (weather, sports, personal questions, etc.)
            
            Consider the conversation history to better understand context. If the user is following up on a previous data-related conversation, classify as 'data_query'.
            
            Return ONLY the category name, nothing else."""
        )
        
        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user question
        messages.append({"role": "user", "content": user_question})
        
        resp = co.chat(
            model="command-r-08-2024",
            messages=messages
        )
        
        intent = resp.message.content[0].text.strip().lower()
        return intent if intent in ['data_query', 'greeting', 'irrelevant'] else 'data_query'
        
    except Exception as e:
        # Default to data_query if classification fails
        return 'data_query'

def generate_contextual_response(user_question: str, intent: str) -> str:
    """Generate a contextual response based on user intent using Cohere"""
    try:
        # Get conversation history for context
        conversation_history = get_session_memory()
        
        if intent == 'data_query':
            system_prompt = (
                """You are a helpful business data assistant. The user is asking about business data analysis, but you don't have access to their specific data right now. Explain that you can help them analyze their sales, customer, and churn data, and ask them to be more specific about what they'd like to know. Be friendly and professional.
                
                Consider the conversation history to provide contextual responses. If they've asked similar questions before, acknowledge that and build upon previous discussions."""
            )
        elif intent == 'greeting':
            system_prompt = (
                """You are a friendly business data assistant. The user is greeting you. Respond naturally and let them know you can help them analyze their business data including sales, customers, and churn metrics. Be conversational and welcoming.
                
                If there's conversation history, acknowledge any previous interactions warmly."""
            )
        else:  # irrelevant
            system_prompt = (
                "You are a business data assistant. The user is asking about something unrelated to business data analysis. Politely acknowledge their question but redirect them to ask about business data, sales, customers, or analytics instead. Be friendly but stay focused on your role."
            )
        
        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user question
        messages.append({"role": "user", "content": user_question})
        
        resp = co.chat(
            model="command-r-08-2024",
            messages=messages
        )
        return resp.message.content[0].text.strip()
        
    except Exception as e:
        return "I'm here to help you analyze your business data. What would you like to know about your sales, customers, or business metrics?"

def execute_sql_query(sql: str) -> tuple[pd.DataFrame, str, bool]:
    """Execute SQL query and return results as DataFrame, status message, and success flag"""
    try:
        print(f"🔍 Executing SQL: {sql}")
        
        # Validate that the input looks like SQL before attempting to execute
        sql_stripped = sql.strip()
        sql_keywords = ['SELECT', 'UPDATE', 'INSERT', 'DELETE', 'WITH', 'CREATE', 'DROP', 'ALTER']
        
        # Check if the input starts with a SQL keyword
        if not any(sql_stripped.upper().startswith(keyword) for keyword in sql_keywords):
            return pd.DataFrame(), f"❌ Error: Received non-SQL input: {sql[:100]}...", False
        
        # Check for obvious natural language patterns that shouldn't be in SQL
        natural_language_patterns = [
            r'\b(In \d{4}, a total of)\b',  # "In 2023, a total of"
            r'\b(This is a significant)\b',  # "This is a significant"
            r'\b(The results show)\b',       # "The results show"
            r'\b(Based on the data)\b',      # "Based on the data"
            r'\b(Looking at the)\b',         # "Looking at the"
        ]
        
        for pattern in natural_language_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return pd.DataFrame(), f"❌ Error: Input appears to be natural language, not SQL: {sql[:100]}...", False
        
        # Clean SQL (remove markdown formatting if present)
        sql_match = re.search(r'```sql\s*(.*?)\s*```', sql, re.DOTALL)
        clean_sql = sql_match.group(1).strip() if sql_match else sql.strip()
        
        print(f"🔍 Clean SQL to execute: {clean_sql}")
        
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
        error_msg = str(e)
        print(f"🔍 SQL execution error: {error_msg}")
        return pd.DataFrame(), f"❌ Error executing SQL: {error_msg}", False
    

def translate_to_english(text: str) -> str:
    """Translate non-English text to English for better SQL generation"""
    try:
        system_prompt = (
            """You are a translator. If the input text is in a language other than English, translate it to English while preserving the exact meaning and context, especially for business and data analysis terms.

            If the text is already in English, return it unchanged.
            
            For business terms:
            - العملاء المتسربين = churned customers
            - يناير = January
            - العملاء = customers
            - المبيعات = sales
            - الإيرادات = revenue
            
            Return ONLY the translated text or original text if already in English."""
        )
        
        resp = co.chat(
            model="command-r-08-2024",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        
        return resp.message.content[0].text.strip()
        
    except Exception as e:
        return text
    



def generate_sql_query(user_question: str) -> str:
    """Generate SQL query using Cohere API with conversation history for context"""
    
    english_question = translate_to_english(user_question)
    
    try:
        # Get conversation history for context
        conversation_history = get_session_memory()
        print(f"🔍 SQL Generation - Conversation History: {conversation_history}")
        print(f"🔍 Current Question: {user_question}")
        print(f"🔍 English Translation: {english_question}")
        
        # Get current date for context
        current_date = datetime.now()
        current_date_str = current_date.strftime('%Y-%m-%d')
        current_month = current_date.strftime('%B %Y')
        last_month = (current_date.replace(day=1) - pd.Timedelta(days=1)).strftime('%B %Y')
        
        system_prompt = (
            f"""You are a SQL generator. Your ONLY job is to generate valid PostgreSQL SQL queries.

            **CRITICAL INSTRUCTIONS**:
            - You MUST return ONLY SQL code - no explanations, no natural language, no markdown
            - Do NOT provide any commentary, analysis, or description
            - Do NOT return results or data - only the SQL query itself
            - Your response should be executable SQL that starts with SELECT, UPDATE, INSERT, etc.
            
            **CURRENT DATE CONTEXT**:
            - Today's date: {current_date_str}
            - Current month: {current_month}
            - Last month: {last_month}
            - Use this context to interpret relative date terms like "last month", "this month", "this quarter", etc.
            
            IMPORTANT RULES:
            1. **Use case-insensitive matching (ILIKE) when filtering text columns like `region` or `segment`**
            2. **For date filtering, use proper date format and column names from the schema**
            3. **Do NOT use user input directly as column values - map them to actual database values**
            4. **For churn analysis, use the correct table structure provided in the schema**
            5. **If asking about churned customers, look for churn-related columns like `churn_status`, `churned`, or similar**
            6. **For time periods, use the actual date columns in the database**
            7. **For product filtering: Use = (exact match) for single letters/numbers, ILIKE for partial text**
                PRODUCT FILTERING EXAMPLES:
                - "Product A" → WHERE product ILIKE 'Product A'
                - "المنتج A" → WHERE product ILIKE 'Product A'
            8. **For region filtering: Use = (exact match) for single letters/numbers, ILIKE for partial text**
                REGION FILTERING EXAMPLES:
                - "Region A" → WHERE region ILIKE 'Region A'
                - "المنطقة A" → WHERE region ILIKE 'Region A'
                - "الشمالية" → WHERE region ILIKE 'North'
            
            **RELATIVE DATE INTERPRETATION**:
            - "last month" = {last_month} = use WHERE EXTRACT(YEAR FROM date) = {(current_date.replace(day=1) - pd.Timedelta(days=1)).year} AND EXTRACT(MONTH FROM date) = {(current_date.replace(day=1) - pd.Timedelta(days=1)).month}
            - "this month" = {current_month} = use WHERE EXTRACT(YEAR FROM date) = {current_date.year} AND EXTRACT(MONTH FROM date) = {current_date.month}
            - "last quarter" = previous complete quarter based on current date
            - Always convert relative terms to specific date ranges
            
            **CRITICAL - YEAR-OVER-YEAR GROWTH CALCULATIONS**:
            - **AVOID complex window functions with GROUP BY** - they cause PostgreSQL errors
            - **For growth percentage between years**, use simple conditional aggregation:
              ```sql
              SELECT 
                  SUM(CASE WHEN EXTRACT(YEAR FROM date) = 2023 THEN revenue ELSE 0 END) AS revenue_2023,
                  SUM(CASE WHEN EXTRACT(YEAR FROM date) = 2024 THEN revenue ELSE 0 END) AS revenue_2024,
                  ((SUM(CASE WHEN EXTRACT(YEAR FROM date) = 2024 THEN revenue ELSE 0 END) - 
                    SUM(CASE WHEN EXTRACT(YEAR FROM date) = 2023 THEN revenue ELSE 0 END)) / 
                   NULLIF(SUM(CASE WHEN EXTRACT(YEAR FROM date) = 2023 THEN revenue ELSE 0 END), 0)) * 100 AS growth_percentage
              FROM sales 
              WHERE EXTRACT(YEAR FROM date) IN (2023, 2024);
              ```
            - **For comparing years**, always use CASE WHEN statements instead of window functions
            - **Use NULLIF() to prevent division by zero errors**
            
            **CRITICAL - CONVERSATION CONTEXT & FOLLOW-UP QUESTIONS**:
            - **ANALYZE the conversation history carefully** to understand what the user previously asked about
            - **INHERIT the same data type, metrics, and structure** from previous queries when user asks follow-up questions
            - **EXAMPLES of follow-up handling**:
                * Previous: "Sales data for January 2024" → Current: "What about February?" → Generate: Sales data for February 2024
                * Previous: "Revenue by region in Q1" → Current: "Show me Q2" → Generate: Revenue by region in Q2
                * Previous: "Product A sales" → Current: "What about Product B?" → Generate: Product B sales with same structure
                * Previous: "Churn in North region" → Current: "How about South?" → Generate: Churn in South region
            - **RECOGNIZE implicit references**: "last month", "next quarter", "same period", "other regions", etc.
            - **MAINTAIN consistency** in date formats, column selections, and aggregation methods from previous queries
            - **BUILD UPON** previous analysis rather than starting fresh each time
            
            Schema Information:
            - Always refer to the actual column names in the database
            - Use proper date filtering with DATE columns
            - Don't assume column names based on the question - use schema column names
            
            REMEMBER: Return ONLY the SQL query, nothing else. No explanations, no markdown, no natural language.
            """
        )
        
        # Build messages array with conversation history but only include SQL-related context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context, but filter to only include SQL queries
        if conversation_history:
            # Only add previous SQL queries for context, not natural language responses
            sql_context = []
            for i, msg in enumerate(conversation_history):
                if msg["role"] == "user":
                    sql_context.append(msg)
                elif msg["role"] == "assistant" and i < len(conversation_history) - 1:
                    # Look for SQL queries in the full messages (which include metadata)
                    full_messages = st.session_state.get('current_messages', [])
                    if i < len(full_messages):
                        full_msg = full_messages[i]
                        if "sql_query" in full_msg:
                            sql_context.append({"role": "assistant", "content": f"Previous SQL: {full_msg['sql_query']}"})
            
            messages.extend(sql_context[-4:])  # Only last 4 messages for context
        else:
            print("🔍 No conversation history available")
        
        # Add current question with schema info and very explicit instructions
        user_prompt = f"""Database Schema:{SCHEMA_INFO}

Original Question: {user_question}
English Translation: {english_question}

Generate ONLY the SQL query to answer this question. Do not include any explanation, description, or analysis. Return pure SQL code only."""
        messages.append({"role": "user", "content": user_prompt})
        
        print(f"🔍 Messages being sent to Cohere: {messages}")
        
        resp = co.chat(
            model="command-r-08-2024",
            messages=messages,
            temperature=0.1  # Lower temperature for more consistent SQL generation
        )
        
        sql = resp.message.content[0].text.strip()
        print(f"🔍 Raw response from Cohere: {sql}")
        
        # Remove any markdown formatting
        sql = re.sub(r'```sql\n?|```\n?', '', sql).strip()
        
        # Validate that the response looks like SQL
        sql_keywords = ['SELECT', 'UPDATE', 'INSERT', 'DELETE', 'WITH']
        if not any(sql.upper().startswith(keyword) for keyword in sql_keywords):
            print(f"⚠️ Warning: Response doesn't look like SQL: {sql}")
            # Try to extract SQL from the response if it's embedded
            sql_match = re.search(r'(SELECT.*?)(?:\n\n|\Z)', sql, re.DOTALL | re.IGNORECASE)
            if sql_match:
                sql = sql_match.group(1).strip()
                print(f"🔍 Extracted SQL: {sql}")
            else:
                return f"Error: AI returned non-SQL response: {sql[:100]}..."
        
        print(f"🔍 Final SQL query: {sql}")
        return sql
        
    except Exception as e:
        print(f"🔍 Exception in generate_sql_query: {str(e)}")
        return f"Error generating SQL: {str(e)}"

def generate_natural_language_response(user_question: str, sql_query: str, df: pd.DataFrame, execution_status: str, success: bool) -> str:
    """Generate a natural language response based on the query results with conversation history"""
    try:
        # Get conversation history for context
        conversation_history = get_session_memory()
        
        if not success:
            return f"I encountered an error while analyzing your data: {execution_status}. Could you try rephrasing your question?"
        
        if df.empty:
            return "I searched your data but didn't find any results matching your criteria. You might want to try a different time period or criteria."
        
        # Convert DataFrame to a clean, readable format for the AI
        data_summary = f"Query returned {len(df)} rows with columns: {', '.join(df.columns)}\n"
        
        # Format the data more cleanly to avoid formatting artifacts
        if len(df) > 0:
            # Convert to a more structured format that won't cause spacing issues
            sample_data = df.head(5)
            
            # Create a clean text representation
            data_rows = []
            for _, row in sample_data.iterrows():
                row_data = []
                for col in df.columns:
                    value = row[col]
                    # Clean up numeric formatting
                    if pd.isna(value):
                        row_data.append("NULL")
                    elif isinstance(value, (int, float)):
                        # Format numbers cleanly
                        if isinstance(value, float):
                            if value.is_integer():
                                row_data.append(str(int(value)))
                            else:
                                row_data.append(f"{value:,.2f}")
                        else:
                            row_data.append(f"{value:,}")
                    else:
                        # Clean up text values
                        row_data.append(str(value).strip())
                data_rows.append(" | ".join(row_data))
            
            # Create clean header and data
            header = " | ".join(df.columns)
            sample_text = f"{header}\n" + "\n".join(data_rows)
            data_summary += f"Sample data:\n{sample_text}"
        
        system_prompt = (
            """You are a friendly business data analyst. Based on a user's question and the query results, provide a conversational summary of the findings. Be helpful, insightful, and highlight key business insights. Keep it natural and easy to understand. Keep your answer short and to the point. Do not go into depths explaining the data results. Keep it simple and concise. Respond in the language of the user's question.

            Respond in the same langauge as the user's question.
            
            **IMPORTANT FORMATTING RULES**:
            - Provide clean, properly formatted text without any spacing artifacts
            - Use proper number formatting (e.g., "25,364.32" not "25, 364.32")
            - Ensure region/location names are properly spaced (e.g., "West" not "W est")
            - Write in clean, natural language without unusual character breaks
            - Numbers should be clearly readable and properly formatted
            
            **CONVERSATION CONTEXT & FOLLOW-UP HANDLING**:
            - **ANALYZE conversation history** to understand if this is a follow-up question
            - **REFERENCE previous findings** when relevant (e.g., "Compared to January's results...", "Building on the previous analysis...")
            - **ACKNOWLEDGE progression** of the analysis (e.g., "Now looking at February data...", "Moving to the next period...")
            - **MAKE CONNECTIONS** between current and previous results when appropriate
            - **IDENTIFY PATTERNS** across time periods or categories if user is comparing
            - **PROVIDE CONTEXT** for follow-up questions (e.g., "This continues the trend from...", "Unlike the previous month...")
            
            **EXAMPLES**:
            - If previous was January sales and current is February sales, say: "Looking at February sales data, here's what I found..."
            - If comparing regions after a previous regional analysis: "Moving to the [new region], the data shows..."
            - For time-based follow-ups: "For this period, the results show..." and compare if relevant"""
        )
        
        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context (excluding the last user message since we're adding it separately)
        if conversation_history:
            # Remove the last message since it's the current question
            context_history = conversation_history[:-1] if len(conversation_history) > 0 else []
            messages.extend(context_history)
        
        # Add current analysis
        user_prompt = f"""
User Question: {user_question}
SQL Query Used: {sql_query}
Results Summary: {data_summary}

Current Date Context:
- Today's date: {datetime.now().strftime('%Y-%m-%d')}
- Current month: {datetime.now().strftime('%B %Y')}
- Last month: {(datetime.now().replace(day=1) - pd.Timedelta(days=1)).strftime('%B %Y')}

Please provide a natural, conversational response summarizing these findings and any business insights. Consider the conversation history to provide contextual analysis. When referring to time periods, be specific about what period was actually analyzed based on the current date context.
"""
        messages.append({"role": "user", "content": user_prompt})
        
        resp = co.chat(
            model="command-r-08-2024",
            messages=messages
        )
        
        response = resp.message.content[0].text.strip()
        
        return response
        
    except Exception as e:
        return f"I found some data for your question ({len(df)} records), but had trouble summarizing it. Could you try asking in a different way?"

def process_user_question(user_question: str):
    """Process user question based on intent"""
    
    # Add user message using session manager
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
        
        # Add assistant response with metadata using session manager
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
        
        # First, let's see what columns exist
        columns_result = session.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'job_logs'")
        ).fetchall()
        
        # Check if the record exists at all
        exists_check = session.execute(
            text("SELECT COUNT(*) FROM job_logs WHERE log_id = :id"),
            {"id": log_id}
        ).fetchone()
        
        # Get the actual record
        r = session.execute(
            text("SELECT * FROM job_logs WHERE log_id = :id"),
            {"id": log_id}
        ).fetchone()
        
        if r:
            
            # Try to get the specific columns you need
            result = session.execute(
                text("SELECT log_id, job_name, run_timestamp, message FROM job_logs WHERE log_id=:id"),
                {"id": log_id}
            ).fetchone()
            
            if result:
                data = dict(result._mapping)
                data["run_timestamp"] = data["run_timestamp"].isoformat()
                return data
            else:
                return {"error": "specific columns not found"}
        else:
            return {"error": "record not found"}
            
    except Exception as e:
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

def explain_incident_agent(log_id: int, language: str = "english") -> str:
    """
    Analyze and explain an incident by fetching log details and providing 
    root cause analysis with resolution steps in the specified language.
    """
    
    # Get conversation history for context
    conversation_history = get_session_memory()
    
    # Language-specific prompts
    if language == "arabic":
        user_msg = (
            f"يرجى تحليل حادثة السجل رقم {log_id}. "
            f"أولاً، احصل على تفاصيل الفشل باستخدام معرف السجل. "
            f"ثم، استخدم رسالة الخطأ للبحث عن معلومات السبب الجذري والحل. "
            f"قدم شرحاً شاملاً يتضمن:\n"
            f"1. تفاصيل المهمة (الاسم، الوقت)\n"
            f"2. تحليل رسالة الخطأ\n"
            f"3. شرح السبب الجذري\n"
            f"4. خطوات الحل التفصيلية\n"
            f"5. الإجراءات الوقائية إن أمكن\n\n"
            f"إذا كان هناك تاريخ محادثة سابق، فاستخدمه لفهم السياق وتقديم تحليل أكثر عمقاً."
        )
        analysis_language_instruction = "يرجى تقديم التقرير باللغة العربية."
    else:
        user_msg = (
            f"Please analyze incident log ID {log_id}. "
            f"First, fetch the failure details using the log ID. "
            f"Then, use the error message to look up root cause and resolution information. "
            f"Provide a comprehensive explanation including:\n"
            f"1. Job details (name, timestamp)\n"
            f"2. Error message analysis\n"
            f"3. Root cause explanation\n"
            f"4. Detailed resolution steps\n"
            f"5. Preventive measures if applicable\n\n"
            f"If there's conversation history, use it to understand context and provide deeper analysis."
        )
        analysis_language_instruction = "Please provide the report in English."
    
    try:
        
        # Build messages array with conversation history
        messages = []
        
        # Add conversation history for context
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current analysis request
        messages.append({"role": "user", "content": user_msg})
        
        # First API call with tools
        first_response = co.chat(
            model="command-r-08-2024",
            messages=messages,
            tools=tool_defs,
            temperature=0.1
        )
        
        
        if not hasattr(first_response, 'message') or first_response.message is None:
            return "Error: No response received from the model"
        
        msg = first_response.message
        tool_calls = getattr(msg, 'tool_calls', None)
        
        
        if not tool_calls or len(tool_calls) == 0:
            # No tool calls made - return direct response or error
            content = getattr(msg, 'content', '')
            return content if content else f"Model didn't make required tool calls for log_id {log_id}"
        
        
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

        # Build complete conversation history including the original context
        conversation = []
        
        # Add conversation history for context
        if conversation_history:
            conversation.extend(conversation_history)
        
        # Add the analysis request
        conversation.append({"role": "user", "content": user_msg})
        conversation.append({
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
        })
        
        # Add all tool results
        conversation.extend(tool_results)
        
        # Add analysis request with language specification
        if language == "arabic":
            analysis_prompt = (
                f"استناداً إلى نتائج الأدوات أعلاه، يرجى تقديم تقرير تحليل شامل للحادثة رقم {log_id}. "
                f"ملخص ما تم استرداده:\n\n{tools_summary}"
                f"يرجى تحليل هذه المعلومات وتقديم:\n"
                f"1. تفاصيل فشل المهمة الكاملة\n"
                f"2. تحليل السبب الجذري\n" 
                f"3. تعليمات الحل خطوة بخطوة\n"
                f"4. الإجراءات الوقائية\n"
                f"5. أي رؤى إضافية\n\n"
                f"إذا كان هناك محادثات سابقة حول حوادث مشابهة، فاربط هذا التحليل بالمعرفة السابقة.\n"
                f"لا تقم بأي استدعاءات أدوات إضافية - فقط قدم تحليلاً مفصلاً باللغة العربية بناءً على البيانات أعلاه. لا تضف عنواناً للتقرير."
            )
        else:
            analysis_prompt = (
                f"Based on the tool execution results above, please provide a comprehensive incident analysis report for log ID {log_id}. "
                f"Here's a summary of what was retrieved:\n\n{tools_summary}"
                f"Please analyze this information and provide:\n"
                f"1. Complete job failure details\n"
                f"2. Root cause analysis\n" 
                f"3. Step-by-step resolution instructions\n"
                f"4. Preventive measures\n"
                f"5. Any additional insights\n\n"
                f"If there are previous conversations about similar incidents, connect this analysis to prior knowledge.\n"
                f"Do not make any additional tool calls - just provide a detailed analysis in English based on the data above. Do not add a report header."
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
        
        return final_content
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return f"Error in incident analysis: {str(e)}\n\nFull traceback:\n{error_trace}"

def render_sidebar():
    """Render the chat history sidebar"""
    with st.sidebar:
        # Get current session ID (needed for highlighting current session)
        session_id = get_or_create_session_id()
        
        # Get current mode for display
        current_mode = st.session_state.get('current_mode', 'SQL Query Assistant')
        
        # Compact sidebar header with status
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h1 style="margin: 0; font-size: 1.4rem; color: white;">
                <span class="status-indicator"></span>المحادثات
            </h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact new chat button
        if st.button("جديد➕", use_container_width=True, type="primary"):
            create_new_chat_session()
            st.rerun()
        
        st.markdown("---")
        
        # Display chat sessions
        all_sessions = load_all_sessions(current_mode)
        
        if all_sessions:
            # Sort sessions by updated time (newest first)
            sorted_sessions = sorted(
                all_sessions.items(),
                key=lambda x: x[1]["updated_at"],
                reverse=True
            )
            
            # Show only recent 5 sessions for cleaner look
            for session_id_item, session_data in sorted_sessions[:5]:
                col1, col2 = st.columns([3.5, 0.5])
                
                with col1:
                    # Session button with current session highlighting
                    is_current = session_id_item == session_id
                    # Truncate title to fit better
                    title = session_data['title'][:25] + "..." if len(session_data['title']) > 25 else session_data['title']
                    button_label = f"{'🟢' if is_current else '💭'} {title}"
                    
                    if st.button(
                        button_label,
                        key=f"session_{session_id_item}",
                        use_container_width=True,
                        type="primary" if is_current else "secondary"
                    ):
                        if session_id_item != session_id:
                            load_session(session_id_item)
                            st.rerun()
                
                with col2:
                    # Compact delete button
                    if st.button("🗑", key=f"delete_{session_id_item}", help="Delete"):
                        if delete_session(session_id_item):
                            st.rerun()
                
                # Compact timestamp and message count
                timestamp_str = session_data["updated_at"].strftime("%m/%d")
                msg_count = session_data.get("message_count", 0)
                st.markdown(f"<small style='color: rgba(255, 255, 255, 0.5); font-size: 0.7rem;'>{timestamp_str} • {msg_count} msg</small>", unsafe_allow_html=True)
                
            # Show more sessions indicator if there are more than 5
            if len(sorted_sessions) > 5:
                st.markdown(f"<small style='color: rgba(255, 255, 255, 0.6); text-align: center; display: block;'>+{len(sorted_sessions) - 5} more sessions</small>", unsafe_allow_html=True)
        else:
            # Empty state
            st.markdown("""
            <div style="text-align: center; color: rgba(255, 255, 255, 0.6); padding: 1rem 0;">
                <p style="margin: 0;">لا توجد محادثات بعد</p>
                <small>ابدأ الدردشة لبناء الذاكرة</small>
            </div>
            """, unsafe_allow_html=True)

def main():
    # Set current mode in session state for module-specific chats
    if 'current_mode' not in st.session_state:
        st.session_state.current_mode = mode
    elif st.session_state.current_mode != mode:
        # Mode changed - save current session and switch context
        save_current_session()
        st.session_state.current_mode = mode
        # Reset session loaded flag to load correct module
        st.session_state.session_loaded = False
        # Force page reload on mode switch
        st.rerun()
    
    # Initialize chat system
    initialize_chat_system()
    
    # Render sidebar
    render_sidebar()
    
    if mode == "SQL Query Assistant":
        # Enhanced SQL Query Assistant UI with RTL support
        st.markdown("""
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="margin: 0;">مساعد الدردشة STC 💬 </h1>
            <p style="color: #6c757d; font-size: 1.2rem; margin-top: 0.5rem; direction: rtl;">
                اطرح أسئلة حول بيانات عملك باللغة الطبيعية
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Welcome cards when no messages
        if not st.session_state.current_messages:
            # Fix for RTL headers while maintaining proper markdown rendering
            st.markdown("""
            <style>
                [data-testid="stMarkdownContainer"] h3 {
                    direction: rtl;
                    text-align: right;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # Use regular markdown for headers - they'll inherit RTL from the style above
            st.markdown("### 🚀 ابدأ")
            
            # Sample questions in cards
            col1, col2, col3 = st.columns(3)
            
            sample_questions = [
                "ما هو إجمالي الإيرادات في 1 يوليو 2024؟",
                "ما هي شرائح العملاء الأعلى تسرباً في يناير 2024؟",
                "أي منطقة حققت أعلى نمو في الإيرادات بين الأرباع في 2024؟?"
            ]
            
            for i, (col, question) in enumerate(zip([col1, col2, col3], sample_questions)):
                with col:
                    if st.button(f"💡 {question}", key=f"sample_{i}", use_container_width=True):
                        try:
                            with st.spinner(" 🤔 جاري معالجة سؤالك"):
                                process_user_question(question)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error processing question: {str(e)}")
                            add_message("assistant", f"I encountered an error while processing your question: {str(e)}")
                            st.rerun()
            
            st.markdown("---")
            st.markdown("### 💡 نصائح للحصول على نتائج أفضل:")
            
            # Content under the tips header
            st.markdown("""
            <div style="direction: rtl; text-align: right;">
            <ul style="list-style-type: disc; padding-right: 20px; margin-right: 20px;">
                <li>كن محددًا بشأن الفترات الزمنية والمقاييس</li>
                <li>اسأل عن بيانات المبيعات أو الإيرادات أو العملاء أو معدل دوران العملاء</li>
                <li>استخدم اللغة الطبيعية - لا حاجة للمصطلحات التقنية</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Display current chat messages with RTL support for Arabic
        for message in st.session_state.current_messages:
            with st.chat_message(message["role"]):
                # Check if content is in Arabic (simple check for Arabic characters)
                is_arabic = any('\u0600' <= c <= '\u06FF' for c in message["content"])
                if is_arabic:
                    st.markdown(f'<div style="direction: rtl; text-align: right;">{message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(message["content"])
                
                # Show optional details for data queries
                if message["role"] == "assistant" and "sql_query" in message:
                    with st.expander("🔍 عرض SQL المولد" if is_arabic else "🔍 View Generated SQL", expanded=False):
                        st.markdown("""
                        <div style="background: #1e1e1e; 
                                    border-radius: 8px; 
                                    border: 1px solid #2d2d2d;
                                    margin-top: 0.5rem;">
                        """, unsafe_allow_html=True)
                        st.code(message["sql_query"], language="sql")
                        st.markdown("</div>", unsafe_allow_html=True)
        
        # Enhanced chat input with RTL placeholder
        if prompt := st.chat_input("💭 اسألني عن بيانات عملك"):
            with st.chat_message("user"):
                # Check if input is Arabic
                is_arabic = any('\u0600' <= c <= '\u06FF' for c in prompt)
                if is_arabic:
                    st.markdown(f'<div style="direction: rtl; text-align: right;">{prompt}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(prompt)
            
            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown('<p class="processing-text">🤔 جاري معالجة سؤالك</p>', unsafe_allow_html=True)
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
            
            st.rerun()
    
    else:
        # Enhanced Data Incident Explainer UI with RTL
        st.markdown("""
        <div style="text-align: center; margin-bottom: 3rem; direction: rtl;">
            <h1 style="margin: 0;"> 🔴 محلل حوادث خط أنابيب البيانات </h1>
            <p style="color: #6c757d; font-size: 1.2rem; margin-top: 0.5rem;">تحليل عمليات تشغيل خط أنابيب البيانات الفاشلة والحصول على خطوات الحل</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Language selector with RTL
        col_left, col_right = st.columns([1, 3])  # Reversed column ratio
        with col_left:
            report_language = st.selectbox(
                "لغة التقرير 📄",
                ["العربية", "English"],
                index=0,
                help="اختر لغة تقرير تحليل الحادث"
            )
        
        # Metrics dashboard with RTL
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
            <div class="metric-card" style="direction: rtl;">
                <div class="metric-value">{total_failures}</div>
                <div class="metric-label">إجمالي الفشل</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="direction: rtl;">
                <div class="metric-value">{recent_failures}</div>
                <div class="metric-label">آخر 24 ساعة</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card" style="direction: rtl;">
                <div class="metric-value">{unique_jobs}</div>
                <div class="metric-label">الوظائف المتضررة</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Failure selection section with RTL
        st.markdown('<h3 style="direction: rtl; text-align: right;">📋 اختر العملية الفاشلة</h3>', unsafe_allow_html=True)
        
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
            # Add RTL styling for selectbox labels
            st.markdown("""
            <style>
                /* RTL support for selectbox labels and content */
                .stSelectbox label {
                    direction: rtl !important;
                    text-align: right !important;
                    width: 100% !important;
                }
                .stSelectbox > div > div {
                    direction: rtl !important;
                    text-align: right !important;
                }
                /* Additional styling for the selectbox container */
                .stSelectbox {
                    direction: rtl !important;
                }
                /* Style for the selectbox options */
                .stSelectbox > div > div > div[role="listbox"] {
                    direction: rtl !important;
                    text-align: right !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            selected = st.selectbox(
                "اختر عملية خط الأنابيب الفاشلة للتحليل:",
                options=options,
                help="اختر من آخر 50 عملية فاشلة",
                label_visibility="visible"
            )
            
            if st.button("🔍 تحليل الحادث", type="primary", use_container_width=True):
                log_id = int(selected.split("|")[0].strip().replace("🔴 ", ""))
                
                # Set Arabic as default language
                language = "english" if "English" in report_language else "arabic"
                
                # Create user message for the incident analysis request
                user_message = f"تحليل الحادثة رقم {log_id}" if language == "arabic" else f"Analyze incident log ID {log_id}"
                add_message("user", user_message, {
                    "log_id": log_id,
                    "analysis_language": language,
                    "incident_type": "pipeline_failure"
                })
                
                with st.spinner('🔄 جاري تحليل الحادث وإنشاء التقرير'):
                    try:
                        explanation = explain_incident_agent(log_id, language)
                        st.markdown('<div style="direction: rtl; text-align: right;">✅ اكتمل التحليل!</div>', unsafe_allow_html=True)
                        
                        # Save the assistant response with metadata
                        add_message("assistant", explanation, {
                            "log_id": log_id,
                            "analysis_language": language,
                            "analysis_type": "incident_report",
                            "success": True
                        })
                        
                    except Exception as e:
                        error_msg = f'حدث خطأ أثناء التحليل: {str(e)}' if language == "arabic" else f'Error during analysis: {str(e)}'
                        st.markdown(f'<div style="direction: rtl; text-align: right;">❌ {error_msg}</div>', unsafe_allow_html=True)
                        explanation = f"حدث خطأ: {str(e)}" if language == "arabic" else f"Error occurred: {str(e)}"
                        
                        # Save the error response with metadata
                        add_message("assistant", explanation, {
                            "log_id": log_id,
                            "analysis_language": language,
                            "analysis_type": "incident_report",
                            "success": False,
                            "error": str(e)
                        })
                
                # Force rerun to show the new messages in the chat interface
                st.rerun()
        else:
            st.info("ℹ️ No failed pipeline runs found in the database.")
        
        # Display current chat messages for incident analysis
        st.markdown("---")
        st.markdown('<h3 style="direction: rtl; text-align: right;">💬 محادثة التحليل</h3>', unsafe_allow_html=True)
        
        for message in st.session_state.current_messages:
            with st.chat_message(message["role"]):
                # Check if content is in Arabic (simple check for Arabic characters)
                is_arabic = any('\u0600' <= c <= '\u06FF' for c in message["content"])
                if is_arabic:
                    st.markdown(f'<div style="direction: rtl; text-align: right;">{message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(message["content"])
                
                # Show metadata for incident analysis
                if message["role"] == "assistant" and "analysis_type" in message:
                    with st.expander("🔍 عرض تفاصيل التحليل" if is_arabic else "🔍 View Analysis Details", expanded=False):
                        metadata = {k: v for k, v in message.items() if k not in ["role", "content", "timestamp", "id"]}
                        st.json(metadata)

    # Render footer
    # render_footer()

if __name__ == "__main__":
    main()
