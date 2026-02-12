# RAG AI Chatbot

A local Retrieval Augmented Generation (RAG) application. This project uses Ollama for the LLM/Embeddings, ChromaDB for vector storage, MinIO for file storage, and Streamlit for the user interface.

## Prerequisites

* [Git](https://git-scm.com)
* [Python 3.11](https://www.python.org/downloads/)
* [Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Quick Start Guide

Run these commands in order to get the application running.

### 1. Spin up Docker containers

docker-compose up -d

### 2. Pull LLM

docker exec -it rag-ollama ollama pull gemma3:4b

### 3. Pull Embedding Model

docker exec -it rag-ollama ollama pull nomic-embed-text

### 4. Create Python virtual environment

python3 -m venv venv

### 5. Activate environment

source venv/bin/activate

### 6. Install dependencies

pip install -r dependencies.txt

### 7. Run application

streamlit run app.py
