import os
import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Date,
    DateTime,
    Integer,
    Text,
    Numeric,
    ForeignKey,
    String,
    JSON,
    Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. "postgresql://user:pass@host:port/db"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# -------------------------------------------------------------------
# Chat Session Management Tables (Simplified)
# -------------------------------------------------------------------
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(36), primary_key=True)  # UUID for the chat session
    title = Column(String(200), nullable=False)
    module = Column(String(50), nullable=False)  # SQL Query Assistant, Data Incident Explainer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    message_id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON)  # Store additional data like SQL queries, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")

# -------------------------------------------------------------------
# Existing Tables
# -------------------------------------------------------------------
class Sales(Base):
    __tablename__ = "sales"
    date       = Column(Date,   primary_key=True)
    region     = Column(Text,   primary_key=True)
    product    = Column(Text,   primary_key=True)
    units_sold = Column(Integer, nullable=False)
    revenue    = Column(Numeric(10, 2), nullable=False)

class Churn(Base):
    __tablename__ = "churn"
    month             = Column(Date, primary_key=True)
    segment           = Column(Text, primary_key=True)
    churned_customers = Column(Integer, nullable=False)

# -------------------------------------------------------------------
# Tables for Use Case #1
# -------------------------------------------------------------------
class Job(Base):
    __tablename__ = "jobs"
    job_name    = Column(Text, primary_key=True)
    description = Column(Text, nullable=False)
    owner       = Column(Text, nullable=False)

class JobLog(Base):
    __tablename__ = "job_logs"
    log_id        = Column(Integer, primary_key=True, autoincrement=True)
    job_name      = Column(Text, ForeignKey("jobs.job_name"), nullable=False)
    run_timestamp = Column(DateTime, nullable=False)
    status        = Column(Text, nullable=False)  # e.g. 'SUCCESS' or 'FAILURE'
    message       = Column(Text, nullable=False)

class IncidentKB(Base):
    __tablename__ = "incident_kb"
    error_pattern = Column(Text, primary_key=True)  # SQL LIKE pattern
    root_cause_en = Column(Text, nullable=False)
    resolution_en = Column(Text, nullable=False)
    root_cause_ar = Column(Text, nullable=False)
    resolution_ar = Column(Text, nullable=False)

# -------------------------------------------------------------------
# Chat Session Management Functions
# -------------------------------------------------------------------
def save_chat_session(db, session_id: str, title: str, module: str, messages: list):
    """Save or update a chat session with its messages"""
    try:
        # Check if chat session exists
        chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        
        if not chat_session:
            # Create new chat session
            chat_session = ChatSession(
                session_id=session_id,
                title=title,
                module=module
            )
            db.add(chat_session)
        else:
            # Update existing
            chat_session.title = title
            chat_session.updated_at = datetime.utcnow()
        
        # Delete existing messages for this session
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        
        # Add messages
        for msg in messages:
            message = ChatMessage(
                message_id=msg.get("id", str(uuid.uuid4())),
                session_id=session_id,
                role=msg["role"],
                content=msg["content"],
                message_metadata=msg.get("metadata", {})
            )
            db.add(message)
        
        db.commit()
        return True
    
    except Exception as e:
        db.rollback()
        print(f"Error saving chat session: {str(e)}")
        return False

def load_chat_session(db, session_id: str):
    """Load a specific chat session with its messages"""
    try:
        chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        
        if not chat_session:
            return None
        
        # Load messages
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
        
        return {
            "session_id": chat_session.session_id,
            "title": chat_session.title,
            "module": chat_session.module,
            "created_at": chat_session.created_at,
            "updated_at": chat_session.updated_at,
            "messages": [
                {
                    "id": msg.message_id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at,
                    "metadata": msg.message_metadata or {}
                }
                for msg in messages
            ]
        }
    
    except Exception as e:
        print(f"Error loading chat session: {str(e)}")
        return None

def load_all_chat_sessions(db, module: str = None):
    """Load all chat sessions, optionally filtered by module"""
    try:
        query = db.query(ChatSession).filter(ChatSession.is_active == True)
        
        if module:
            query = query.filter(ChatSession.module == module)
        
        chat_sessions = query.order_by(ChatSession.updated_at.desc()).all()
        
        result = {}
        for chat in chat_sessions:
            result[chat.session_id] = {
                "title": chat.title,
                "module": chat.module,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
                "message_count": len(chat.messages)
            }
        
        return result
    
    except Exception as e:
        print(f"Error loading chat sessions: {str(e)}")
        return {}

def delete_chat_session(db, session_id: str):
    """Soft delete a chat session"""
    try:
        chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        
        if chat_session:
            chat_session.is_active = False
            db.commit()
            return True
        return False
    
    except Exception as e:
        db.rollback()
        print(f"Error deleting chat session: {str(e)}")
        return False

# -------------------------------------------------------------------
# Initialization
# -------------------------------------------------------------------
def init_db():
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)


# -------------------------------------------------------------------
# Script entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("✅ All tables created including chat session management tables.")
