# RAG AI Chatbot

A fully local **Retrieval-Augmented Generation (RAG)** chatbot application.

This project combines:

- **Ollama** – Local LLM and embedding models  
- **LlamaIndex** – RAG orchestration framework  
- **ChromaDB** – Vector database  
- **MinIO** – Object/file storage. 
- **Docling** – Document parsing and preprocessing. 
- **Streamlit** – Web user interface  

The entire stack runs locally using Docker.

---

## 🏗️ Architecture Overview

User  →  Streamlit UI  
            ↓  
        MinIO (Raw Document Storage)  
            ↓  
        Docling (Parsing & Structured Extraction)  
            ↓  
        LlamaIndex (Chunking + Embeddings via Ollama)  
            ↓  
        ChromaDB (Vector Storage)

---

## ✅ Prerequisites

Make sure the following are installed:

- [Git](https://git-scm.com)
- [Python 3.11](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

> Ensure Docker Desktop is running before proceeding.

---

# 🚀 Quick Start Guide

Follow the steps below **in order** to start the application.

---

## 1️⃣ Start Docker Services

Spin up all required services (Ollama, ChromaDB, MinIO):

```bash
docker-compose up -d
```

Verify containers are running:

```bash
docker ps
```

---

## 2️⃣ Choose and Pull an LLM (Based on Your System Resources)

By default, this project uses:

- LLM: `gemma3:4b`
- Embedding model: `nomic-embed-text`

```bash
docker exec -it rag-ollama ollama pull gemma3:4b
```

However, you may need to choose a different model depending on your hardware. 
Visit https://ollama.com/library for available models.  

If pulling a different model, be sure to update the LLM model constant inside app.py to match the model you selected

```python
LLM_MODEL = "gemma3:4b"
```

Make sure the model name matches exactly what you pulled.

---

## 3️⃣ Pull the Embedding Model

The embedding model is lightweight and works well for most systems:

```bash
docker exec -it rag-ollama ollama pull nomic-embed-text
```

If you wish to experiment with other embedding models, update the embedding model constant accordingly.

```python
EMBED_MODEL = "nomic-embed-text"
```

---

## 4️⃣ Create a Python Virtual Environment

```bash
python3 -m venv venv
```

---

## 5️⃣ Activate the Virtual Environment

**Mac/Linux:**

```bash
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
venv\Scripts\Activate.ps1
```

---

## 6️⃣ Install Python Dependencies

```bash
pip install -r dependencies.txt
```

---

## 7️⃣ Run the Application

```bash
streamlit run app.py
```

Then open:

```
http://localhost:8501
```

---

# 📦 Services Overview

| Service     | Purpose |
|-------------|----------|
| Ollama      | Runs local LLMs and generates embeddings |
| ChromaDB    | Stores and retrieves vector embeddings for similarity search |
| MinIO       | Stores raw uploaded documents as object storage |
| Docling     | Parses, extracts, and structures document content before indexing |
| LlamaIndex  | Orchestrates document chunking, embedding, retrieval, and prompt assembly |
| Streamlit   | Provides the web-based user interface |

---

# 🧠 Model Selection Guide

If your system feels slow or crashes:

- Use a smaller model (2B–4B)
- Close other memory-heavy applications
- Avoid running multiple large Docker containers
- Consider enabling GPU acceleration in Docker (if available)

If you have a dedicated GPU:

- You can run larger models (7B–13B)
- Ensure Ollama is configured to use GPU
- Monitor memory usage during inference

Visit https://ollama.com/library for available models.

---

# 🛑 Stopping the Application

To stop all Docker services:

```bash
docker-compose down
```

To remove volumes as well:

```bash
docker-compose down -v
```

---

# 🔧 Troubleshooting

### Docker not running?
Ensure Docker Desktop is open and running.

### Model not found errors?
Re-run the `ollama pull` command inside the container.

### Port already in use?
Check if another Streamlit instance is running:

```bash
lsof -i :8501
```

### Out of Memory (OOM) errors?
Switch to a smaller LLM (e.g., 2B or 4B).

---

# 📄 License

This project is licensed under the MIT License.  
See the [LICENSE](./LICENSE) file for details.

---

## 🗂️ Viewing Stored Files in MinIO

All uploaded documents are stored as raw objects in MinIO.

You can view and manage these files through the MinIO Web Console:

```
http://localhost:9001

Username: minioadmin
Password: minioadmin
```

# 📬 Logs

View Ollama logs:

```bash
docker logs rag-ollama
```

#

---
