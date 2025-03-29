from langchain_ollama import ChatOllama
from .settings import settings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List
from langchain_core.documents import Document
import os
from .pgvector_utils import vector_store

retriever = vector_store.as_retriever(search_kwargs={"k": 2})

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Use the following context to answer the user's question."),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

def get_rag_chain(model: str):
    """
    Creates a Retrieval-Augmented Generation (RAG) chain using an Ollama model and a PGVector vector store.

    The RAG chain consists of a history-aware retriever followed by a question answer chain.
    The history-aware retriever uses the PGVector vector store to retrieve relevant documents based on the chat history.
    The question answer chain takes the output of the retriever and uses it to generate an answer to the user's question.

    Args:
        model (str): The name of the Ollama model to use.
    """
    llm = ChatOllama(
        model=model,
        base_url=settings.ollama_url
    )
    
    # Create a history-aware retriever that uses the PGVector vector store to retrieve relevant documents
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    # Create a question answer chain that takes the output of the retriever and uses it to generate an answer
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    # Create the RAG chain by combining the history-aware retriever and the question answer chain
    """
    The create_retrieval_chain ensures that the retriever (or history-aware retriever) is invoked first to fetch the documents.
    The retrieved documents are then seamlessly passed as the "context" to the qa_prompt in the question-answering chain.
    """
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)    
    return rag_chain
