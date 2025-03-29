from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ModelName(str, Enum):
    Ollama_LLM_model1: str = "gemma3:4b"
    Ollama_LLM_model2: str = "gemma3:1b"
    Ollama_embedding_model: str = "mxbai-embed-large"

class QueryInput(BaseModel):
    prompt: str
    session_id: str = Field(default=None)
    model: ModelName = Field(default=ModelName.Ollama_LLM_model1)

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: ModelName

class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: datetime

class DeleteFileRequest(BaseModel):
    file_id: int