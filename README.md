# LLM RAG CHATBOT

A personal project that integrates a large language model with a retrieval-augmented generation (RAG) approach to provide context-aware chatbot responses. This project leverages FastAPI for the backend, LangChain for LLM integration and RAG chain implementation, Streamlit for the frontend, PostgreSQL with PGVector for document indexing, and Ollama for running the LLM locally. It is deployed using Docker Compose.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [File Structure](#file-structure)
- [API Endpoints](#api-endpoints)
- [Installation and Setup](#installation-and-setup)
- [Usage](#usage)
- [Deployment](#deployment)

## Overview

LLM RAG CHATBOT is designed to deliver high-quality, context-enriched responses by combining:
- **Generative capabilities:** Powered by a local LLM managed via Ollama.
- **Retrieval augmentation:** Enhancing responses by retrieving relevant documents indexed in PostgreSQL (with PGVector extension).

The system is split into two main components:
- **Backend (FastAPI):** Implements API endpoints, handles chat interactions, document uploads, indexing, and deletion.
- **Frontend (Streamlit):** Provides a user-friendly interface for chat interaction and document management.

## Tech Stack

- **Backend:**
  - [FastAPI](https://fastapi.tiangolo.com/) – API framework
  - [LangChain](https://langchain.readthedocs.io/) – LLM integration and RAG chain implementation
- **Frontend:**
  - [Streamlit](https://streamlit.io/) – Interactive user interface
- **Database:**
  - [PostgreSQL](https://www.postgresql.org/) with [PGVector](https://github.com/pgvector/pgvector) extension – Document indexing and vector storage
- **AI Tool:**
  - [Ollama](https://ollama.com/) – Set up and run the LLM locally
- **Deployment:**
  - [Docker Compose](https://docs.docker.com/compose/) – Container orchestration

## File Structure
LLM_RAG_CHATBOT/
│
├───backend/
│   │___dockerfile
│   │___requirements.txt
│   │
│   └───app/
│       │__.env_example         # Example file, rename to .env
│       │___db_utils.py         # Handles database operations
│       │___langchain_utils.py  # Implements the LangChain-specific logic
│       │___main.py             # Entry point of FastAPI application, defines the API routes    
│       │___pgvector_utils.py   # Interacts with the PGVector vector store
│       │___pydantic_models.py  # Defines Pydantic models for request and response validation
│       │___settings.py         
│
│───frontend/
│    │___dockerfile
│    │___requirements.txt
│    │
│    └───app/
│        │___api_utils.py       # Interacts with FastAPI backend
│        │___chat_interface.py  # Chat interaction
│        │___sidebar.py         # Handles document management and model selection:
│        │___streamlit_app.py   # Entry point for Streamlit application   
│      
│___.env_example        # Example file, rename to .env
│___.gitignore
│___docker-compose.yaml  # Service orchestration
│___README

## API Endpoints

### `/chat`
- **Purpose:** Handles chat interactions.
- **Workflow:**
  - Generates a session ID if not provided.
  - Retrieves chat history.
  - Invokes the RAG chain via LangChain to generate a response.
  - Logs the interaction.
  - Returns the generated response.

### `/upload-doc`
- **Purpose:** Manages document uploads.
- **Workflow:**
  - Validates allowed file types.
  - Saves the file temporarily.
  - Indexes the document in the PGVector store.
  - Updates the document record in the PostgreSQL database.

### `/list-docs`
- **Purpose:** Returns a list of all indexed documents.
- **Workflow:** 
  - Fetches and returns document records from the database.

### `/delete-doc`
- **Purpose:** Deletes a specified document.
- **Workflow:**
  - Removes the document from the database.
  - Deletes the document from the PGVector index.

## Installation and Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Steps

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/DuyPhamQuang/LLM-RAG-CHATBOT.git
   cd LLM_RAG_CHATBOT

2. **Configure Environment Variables:**

    Rename .env_example files to .env in both the root and the backend directories.
    Update the configuration as needed.

## Usage

### Running with Docker Compose

1. **Build and Start Containers:**
    ```bash
    docker-compose up -d

2. **Access the Application:**

-  Streamlit UI: Open your browser at http://localhost:8501 to interact with the chatbot and manage documents.
-  FastAPI Backend: The API is available at the port specified in your configuration.
-  Ollama: Access ollama container to pull any models that you want. After that go to the pydantic_models.py file
in backend to add or reconfigure the model name. Then go to sidebar.py file in frontend to add the model to model_options
or just reconfigure it. 
* Note: You still need to own a decent hardwares (GPUs) to run these local LLM models. So pay
attention to that before running any models with large number of tokens.

## Deployment

The project is fully containerized and can be deployed on any system that supports Docker. Use the provided docker-compose.yaml file for seamless deployment across different environments.