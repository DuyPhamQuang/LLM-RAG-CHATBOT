import os
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, TEXT, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Load environment variables
load_dotenv(override=True, verbose=True)

# Database connection using environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

# Database models
class ApplicationLog(Base):
    __tablename__ = 'application_logs'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(TEXT, nullable=False)
    user_query = Column(TEXT, nullable=False)
    LLM_response = Column(TEXT, nullable=False)
    model = Column(TEXT, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class DocumentStore(Base):
    __tablename__ = 'document_store'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(TEXT, nullable=False)
    upload_timestamp = Column(DateTime, server_default=func.now())

# Function to initialize the database tables
def init_db():
    Base.metadata.create_all(bind=engine)

def insert_application_logs(db: Session, session_id: str, user_query: str, LLM_response: str, model: str):
    """
    Inserts chat logs into the application_logs table.
    """
    log = ApplicationLog(
        session_id=session_id,
        user_query=user_query,
        LLM_response=LLM_response,
        model=model
    )
    db.add(log)
    db.commit()

def get_chat_history(db: Session, session_id: str):
    """
    Retrieves chat history for a given session_id.
    Returns a list of messages with roles "human" and "ai".
    """
    logs = db.query(ApplicationLog).filter_by(session_id=session_id).order_by(ApplicationLog.created_at).all()
    history = []
    for log in logs:
        history.append({"role": "human", "content": log.user_query})
        history.append({"role": "ai", "content": log.LLM_response})
    return history

def insert_document_record(db: Session, filename: str):
    """
    Inserts a document filename into the document_store table and returns the inserted file_id.
    """
    doc = DocumentStore(filename=filename)
    db.add(doc)
    db.commit()
    db.refresh(doc)  # Ensure the ID is populated
    return doc.id

def delete_document_record(db: Session, file_id: int):
    """
    Deletes a document record from the document_store table by file_id.
    Returns True if the record was deleted, False otherwise.
    """
    doc = db.query(DocumentStore).filter(DocumentStore.id == file_id).first()
    if doc:
        db.delete(doc)
        db.commit()
        return True
    return False

def get_all_documents(db: Session):
    """
    Retrieves all documents from the document_store table.
    Returns a list of dictionaries with id, filename, and upload_timestamp.
    """
    documents = db.query(DocumentStore).all()
    return [{"id": doc.id, "filename": doc.filename, "upload_timestamp": doc.upload_timestamp} for doc in documents]


