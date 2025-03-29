from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from .langchain_utils import get_rag_chain
from .pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from .db_utils import (insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record,
                      init_db, SessionLocal)
from .pgvector_utils import index_document_to_pgvector, delete_doc_from_pgvector
from sqlalchemy.orm import Session
import os
import uuid
import logging
import shutil

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(swagger_ui_parameters={"syntaxHighlight": False})

def get_db():
    """
    Get a database session.

    This function returns a generator that provides a database session. The session
    is closed automatically when the generator is exhausted.

    Yields:
        A database session (Session)
    """
    db = SessionLocal()
    try:
        # Yield the session to the caller. This allows the caller to use the session as a context manager.
        yield db
    finally:
        # Close the session when the generator is exhausted.
        db.close()

"""Initialize the model on startup."""
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        logging.info("Model initialization completed")
    except Exception as e:
        logging.error(f"Error during startup: {str(e)}")
        raise

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput, db: Session = Depends(get_db)):
    """
    Handle chat requests and return AI-generated responses.

    Args:
        query_input (QueryInput): The input data for the chat, including session ID, question, and model information.
        db (Session): The database session used for retrieving and storing data.

    Returns:
        QueryResponse: The response containing the AI-generated answer, session ID, and model used.
    """
    # Generate or retrieve the session ID, creating a new one if not provided
    session_id = query_input.session_id or str(uuid.uuid4())
    # Log the session ID, user query, and model being used
    logging.info(f"Session ID: {session_id}, User Query: {query_input.prompt}, Model: {query_input.model.value}")

    # Retrieve chat history for the session from the database
    chat_history = get_chat_history(db, session_id)

    # Get the Retrieval-Augmented Generation (RAG) chain based on the specified model
    rag_chain = get_rag_chain(query_input.model.value)

    # Invoke the RAG chain to get the AI-generated response based on user input and chat history
    response = rag_chain.invoke({
        "input": query_input.prompt,
        "chat_history": chat_history
    })

    # Extract the answer from the response
    answer = response['answer']

    # Insert a log entry into the application logs for monitoring and analysis
    insert_application_logs(db, session_id, query_input.prompt, answer, query_input.model.value)
    # Log the session ID and AI-generated response
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")

    # Return the response wrapped in a QueryResponse object
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)

@app.post("/upload-doc")
async def upload_and_index_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload and index a document.

    This endpoint allows the user to upload a document file, which is then saved
    temporarily, indexed, and stored with a unique identifier.

    Args:
        file (UploadFile): The document file to be uploaded.

    Returns:
        dict: A dictionary containing a success message and the file ID if the operation
        is successful.

    Raises:
        HTTPException: If the file type is unsupported or if indexing fails.
    """
    allowed_extensions = ['.pdf', '.docx', '.html']
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Check if the file extension is allowed
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    # Determine temp_file_path
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    temp_file_path = os.path.join(upload_dir, file.filename)

    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Insert the document record and obtain a unique file ID
        file_id = insert_document_record(db, file.filename)

        # Index the document to Pgvector
        success = index_document_to_pgvector(temp_file_path, file_id)

        if success:
            # Return a success message and the file ID if indexing is successful
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            # If indexing fails, delete the document record and raise an exception
            delete_document_record(db, file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs", response_model=list[DocumentInfo], summary="Get a list of all indexed documents")
def list_documents(db: Session = Depends(get_db)) -> list[DocumentInfo]:
    """
    Get a list of all indexed documents.

    This endpoint returns a list of DocumentInfo objects, each containing the file ID, file name, and file extension
    of the indexed document.

    Args:
        db (Session): The database session to use for the query.

    Returns:
        list[DocumentInfo]: A list of DocumentInfo objects, each containing the file ID, file name, and file extension
            of the indexed document.
    """
    return get_all_documents(db)

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest, db: Session = Depends(get_db)):
    """
    Delete a document from the system.

    This endpoint will delete a document from the system. This includes deleting the document from the database and from the Pgvector index.

    Args:
        request (DeleteFileRequest): The DeleteFileRequest object containing the file ID of the document to be deleted.
        db (Session): The database session to use for the query.

    Returns:
        dict: A dictionary containing a message or an error message depending on whether the deletion is successful or not.
    """
    # Delete the document from Pgvector first
    pgvector_delete_success = delete_doc_from_pgvector(db, request.file_id)

    # Check if the deletion from Pgvector was successful
    if pgvector_delete_success:
        # Delete the document record from the database
        db_delete_success = delete_document_record(db, request.file_id)

        # Check if the deletion from the database was successful
        if db_delete_success:
            # Return a success message if the deletion was successful
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            # Return an error message if the deletion failed from the database
            return {"error": f"Deleted from Pgvector but failed to delete document with file_id {request.file_id} from the database."}
    else:
        # Return an error message if the deletion failed from Pgvector
        return {"error": f"Failed to delete document with file_id {request.file_id} from Pgvector."}

