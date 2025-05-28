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
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for sidebar width and chat input styling
st.markdown("""
<style>
    /* Reduce sidebar width */
    .css-1d391kg {
        width: 250px;
    }
    
    /* Increase chat input size */
    .stChatInput > div > div > textarea {
        min-height: 60px !important;
        font-size: 16px !important;
    }
    
    /* Chat input container styling */
    .stChatInput {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# File path for persistent storage
CHAT_STORAGE_FILE = Path("chat_sessions.pkl")

# Initialize Cohere client
@st.cache_resource
def init_cohere_client():
    """Initialize Cohere client with caching"""
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        st.error("❌ COHERE_API_KEY environment variable not set!")
        st.stop()
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
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = str(uuid.uuid4())
    
    if "chat_sessions" not in st.session_state:
        # Load from file
        st.session_state.chat_sessions = load_chat_sessions_from_file()
    
    if "current_messages" not in st.session_state:
        # If we have a current chat ID, try to load its messages
        if (st.session_state.current_chat_id in st.session_state.chat_sessions):
            st.session_state.current_messages = st.session_state.chat_sessions[st.session_state.current_chat_id]["messages"].copy()
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
        # Create a title from the first user message (truncated)
        first_user_msg = next((msg for msg in st.session_state.current_messages if msg["role"] == "user"), None)
        if first_user_msg:
            title = first_user_msg["content"][:40] + "..." if len(first_user_msg["content"]) > 40 else first_user_msg["content"]
        else:
            title = f"Chat {datetime.now().strftime('%H:%M')}"
        
        st.session_state.chat_sessions[st.session_state.current_chat_id] = {
            "title": title,
            "messages": st.session_state.current_messages.copy(),
            "timestamp": datetime.now()
        }
        
        # Save to file
        save_chat_sessions_to_file(st.session_state.chat_sessions)

def load_chat(chat_id):
    """Load a specific chat session"""
    # Save current chat first
    save_current_chat()
    
    # Load selected chat
    if chat_id in st.session_state.chat_sessions:
        st.session_state.current_chat_id = chat_id
        st.session_state.current_messages = st.session_state.chat_sessions[chat_id]["messages"].copy()
    else:
        st.session_state.current_chat_id = chat_id
        st.session_state.current_messages = []

def delete_chat(chat_id):
    """Delete a chat session"""
    if chat_id in st.session_state.chat_sessions:
        del st.session_state.chat_sessions[chat_id]
        
        # Save to file
        save_chat_sessions_to_file(st.session_state.chat_sessions)
        
        # If we're deleting the current chat, create a new one
        if st.session_state.current_chat_id == chat_id:
            create_new_chat()

def classify_user_intent(user_question: str) -> str:
    """Classify user intent to determine if it's data-related, greeting, or irrelevant"""
    try:
        system_prompt = (
            "You are a classifier for user intents in a data analysis chat system. "
            "Classify the user's message into one of these categories:\n"
            "- 'data_query': Questions about data, analytics, sales, revenue, customers, churn, products, regions, etc.\n"
            "- 'greeting': Greetings, hellos, how are you, etc.\n"
            "- 'irrelevant': Questions not related to data analysis (weather, sports, personal questions, etc.)\n"
            "Return ONLY the category name, nothing else."
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
                "You are a helpful business data assistant. The user is asking about business data analysis, "
                "but you don't have access to their specific data right now. Explain that you can help them "
                "analyze their sales, customer, and churn data, and ask them to be more specific about what "
                "they'd like to know. Be friendly and professional."
            )
        elif intent == 'greeting':
            system_prompt = (
                "You are a friendly business data assistant. The user is greeting you. Respond naturally "
                "and let them know you can help them analyze their business data including sales, customers, "
                "and churn metrics. Be conversational and welcoming."
            )
        else:  # irrelevant
            system_prompt = (
                "You are a business data assistant. The user is asking about something unrelated to business "
                "data analysis. Politely acknowledge their question but redirect them to ask about business "
                "data, sales, customers, or analytics instead. Be friendly but stay focused on your role."
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
                return pd.DataFrame(), "No rows returned from the query.", True
            
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=cols)
            return df, f"Query executed successfully. Found {len(df)} rows.", True
            
        finally:
            session.close()
            
    except Exception as e:
        return pd.DataFrame(), f"Error executing SQL: {str(e)}", False

def generate_sql_query(user_question: str) -> str:
    """Generate SQL query using Cohere API"""
    try:
        system_prompt = (
            "You are a SQL assistant. Given a natural-language question and a database schema, "
            "generate a valid PostgreSQL query. Return ONLY the SQL query, no explanation or markdown formatting."
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
            "You are a friendly business data analyst. Based on a user's question and the query results, "
            "provide a conversational summary of the findings. Be helpful, insightful, and highlight key "
            "business insights. Keep it natural and easy to understand."
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

def render_sidebar():
    """Render the chat history sidebar"""
    with st.sidebar:
        st.title("💬 Chats")
        
        # New chat button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            create_new_chat()
            st.rerun()
        
        st.divider()
        
        # Display chat sessions
        if st.session_state.chat_sessions:
            # Sort chats by timestamp (newest first)
            sorted_chats = sorted(
                st.session_state.chat_sessions.items(),
                key=lambda x: x[1]["timestamp"],
                reverse=True
            )
            
            for chat_id, chat_data in sorted_chats:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Chat button with current chat highlighting
                    is_current = chat_id == st.session_state.current_chat_id
                    button_label = f"{'🟢 ' if is_current else ''}{chat_data['title']}"
                    
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
                    # Delete button
                    if st.button("🗑️", key=f"delete_{chat_id}", help="Delete chat"):
                        delete_chat(chat_id)
                        st.rerun()
                
                # Show timestamp
                st.caption(chat_data["timestamp"].strftime("%m/%d %H:%M"))
                st.divider()
        else:
            st.info("No chat history yet. Start a conversation!")

def main():
    # Initialize chat system
    initialize_chat_system()
    
    # Render sidebar
    render_sidebar()
    
    # Main chat interface
    st.title("💬 Chat Assistant")
    
    # Display current chat messages
    for message in st.session_state.current_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show optional details for data queries
            if message["role"] == "assistant" and "sql_query" in message:
                
                with st.expander("View details", expanded=False):
                    # Show data if available
                    if "data" in message and not message["data"].empty:
                        
                        # Create tabs for different views
                        tab1, tab2 = st.tabs(["📋 Data", "📥 Export"])
                        
                        with tab1:
                            st.dataframe(message["data"], use_container_width=True)
                            st.caption(f"{len(message['data'])} rows")
                        
                        with tab2:
                            csv = message["data"].to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"data_{message['timestamp'].strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key=f"download_{message['id']}"
                            )
                            
                            # Show SQL query
                            st.markdown("**Generated SQL:**")
                            st.code(message["sql_query"], language="sql")
    
    # Chat input
    if prompt := st.chat_input("Ask me about your business data..."):
        # Process the question and add to current chat
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            # Show a temporary placeholder while processing
            placeholder = st.empty()
            placeholder.markdown("*Processing your question...*")
            
            # Process the question
            process_user_question(prompt)
            
            # Clear placeholder and show the actual response
            placeholder.empty()
            latest_response = st.session_state.current_messages[-1]
            st.markdown(latest_response["content"])
            
            # Show details if it's a data query
            if "sql_query" in latest_response:
                with st.expander("View details", expanded=False):
                    if "data" in latest_response and not latest_response["data"].empty:
                        tab1, tab2 = st.tabs(["📋 Data", "📥 Export"])
                        
                        with tab1:
                            st.dataframe(latest_response["data"], use_container_width=True)
                            st.caption(f"{len(latest_response['data'])} rows")
                        
                        with tab2:
                            csv = latest_response["data"].to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"data_{latest_response['timestamp'].strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key=f"download_latest_{latest_response['id']}"
                            )
                            
                            st.markdown("**Generated SQL:**")
                            st.code(latest_response["sql_query"], language="sql")
        
        # Save the current chat and rerun to update sidebar
        save_current_chat()
        st.rerun()

if __name__ == "__main__":
    main() 