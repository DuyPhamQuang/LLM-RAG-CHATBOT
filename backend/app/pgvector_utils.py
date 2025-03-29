from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from .pydantic_models import ModelName
from .settings import settings
from pathlib import Path
from typing import List
from langchain_core.documents import Document
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text

# Initialize text splitter and embedding function
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
embeddings = OllamaEmbeddings(model = ModelName.Ollama_embedding_model, base_url=settings.ollama_url)

# Load environment variables
load_dotenv(override=True, verbose=True)

# Debugging: Print the loaded values
print("Loaded environment variables:")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")


# Database connection using environment variables
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
connection = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"  # Uses psycopg3!
collection_name = "my_docs"

#Initialize PG_Vector vector store
vector_store = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
)

def load_and_split_document(file_path: str) -> List[Document]:
    """
    Load and split a document into smaller chunks based on file type.

    Args:
        file_path (str): The path to the document file.

    Returns:
        List[Document]: A list of document chunks.

    Raises:
        ValueError: If the file type is unsupported.
    """
    # Determine the appropriate loader based on file extension
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
    else:
        # Raise an error if the file type is unsupported
        raise ValueError(f"Unsupported file type: {file_path}")

    # Load the document using the selected loader
    documents = loader.load()
    # Split the document into smaller chunks
    return text_splitter.split_documents(documents)

def index_document_to_pgvector(file_path: str, file_id: int) -> bool:
    """
    Indexes a document in the PG_Vector vector store.

    Args:
        file_path (str): The path to the document file.
        file_id (int): The unique identifier for the document.

    Returns:
        bool: True if the document was indexed successfully, False otherwise.
    """
    try:
        # Load and split the document into smaller chunks
        splits = load_and_split_document(file_path)

        # Add metadata to each split
        for split in splits:
            # Add the file_id to each split for later retrieval
            split.metadata['file_id'] = file_id

        # Add the document chunks to the vector store
        vector_store.add_documents(splits)
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False

def delete_doc_from_pgvector(db: Session, file_id: int) -> bool:
    """
    Deletes a document with the specified file_id from the PGVector vector store.

    Args:
        db (Session): SQLAlchemy session to execute the deletion.
        file_id (int): The unique identifier for the document to delete.

    Returns:
        bool: True if the document was deleted successfully, False otherwise.
    """
    try:
        # Find the collection_id for the given collection_name
        collection_query = db.execute(
            text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
            {"name": collection_name}  # Ensure collection_name is defined in your scope
        )
        collection_row = collection_query.fetchone()
        if not collection_row:
            print(f"Collection '{collection_name}' not found")
            return False
        collection_id = collection_row[0]

        # Delete embeddings where collection_id matches and cmetadata['file_id'] = file_id
        delete_query = text("""
            DELETE FROM langchain_pg_embedding
            WHERE collection_id = :collection_id
            AND cmetadata->>'file_id' = :file_id
        """)
        db.execute(
            delete_query,
            {"collection_id": str(collection_id), "file_id": str(file_id)}
        )
        db.commit()
        print(f"Deleted all documents with file_id {file_id}")
        return True
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from PGVector: {str(e)}")
        return False