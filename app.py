import streamlit as st
import boto3
import io
import os
import tempfile
import chromadb
from botocore.config import Config
from botocore.exceptions import ClientError
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.readers.docling import DoclingReader


# --- CONFIGURATION ---
MINIO_URL = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "rag-docs"

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
COLLECTION_NAME = "rag_collection"

OLLAMA_URL = "http://localhost:11434"
LLM_MODEL = "gemma3:4b"
EMBED_MODEL = "nomic-embed-text"

# --- SETUP LLAMAINDEX ---
Settings.embed_model = OllamaEmbedding(
    model_name=EMBED_MODEL,
    base_url=OLLAMA_URL
)
Settings.llm = Ollama(
    model=LLM_MODEL,
    base_url=OLLAMA_URL,
    request_timeout=360.0
)

# --- SETUP S3 (MinIO) ---
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

try:
    s3.head_bucket(Bucket=BUCKET_NAME)
except ClientError:
    s3.create_bucket(Bucket=BUCKET_NAME)

# --- HELPER FUNCTIONS ---
def get_presigned_url(filename: str) -> str:
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": filename},
            ExpiresIn=3600,
        )
    except ClientError:
        return "#"

def list_documents():
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        return [obj['Key'] for obj in response.get('Contents', [])]
    except ClientError:
        return []

def delete_document(filename: str):
    """Removes file from both MinIO (Storage) and ChromaDB (Memory)"""
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
        db = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = db.get_collection(COLLECTION_NAME)
        collection.delete(where={"filename": filename})
        return True
    except Exception as e:
        st.error(f"Error deleting {filename}: {e}")
        return False

# --- UI SETUP ---
st.set_page_config(page_title="RAG AI Chatbot", layout="wide")
st.title("🤖 RAG AI Chatbot")
st.caption(f"Upload files to the knowledge base, then ask questions!")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = []

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "pending_file" not in st.session_state:
    st.session_state.pending_file = None

def process_input():
    if st.session_state.user_input:
        user_text = st.session_state.user_input
        st.session_state.prompt_history.append(user_text)
        st.session_state.messages.append({"role": "user", "content": user_text})

# --- SIDEBAR ---
with st.sidebar:
    st.header("Upload Document")
    
    uploaded_file = st.file_uploader(
        "Drag & Drop PDF/Docs", 
        type=["pdf", "docx", "xlsx"], 
        key=f"uploader_{st.session_state.uploader_key}"
    )

    if uploaded_file:
        st.session_state.pending_file = {
            "name": uploaded_file.name,
            "data": uploaded_file.getvalue()
        }
        st.session_state.uploader_key += 1
        st.rerun()

    if st.session_state.pending_file:
        file_payload = st.session_state.pending_file
        filename = file_payload["name"]
        file_bytes = file_payload["data"]
        
        try:
            with st.spinner(f"🧠 Processing {filename}..."):
                s3.upload_fileobj(io.BytesIO(file_bytes), BUCKET_NAME, filename)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                reader = DoclingReader()
                documents = reader.load_data(tmp_path)
                for doc in documents:
                    doc.metadata["filename"] = filename
                    doc.metadata["source"] = f"s3://{BUCKET_NAME}/{filename}"

                db = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
                chroma_collection = db.get_or_create_collection(COLLECTION_NAME)
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                VectorStoreIndex.from_documents(documents, storage_context=storage_context)

                os.remove(tmp_path)
            
            st.toast(f"✅ Indexed {filename}!", icon="🎉")

        except Exception as e:
            st.error(f"Processing failed: {e}")
        
        st.session_state.pending_file = None
        st.rerun()

    st.divider()
    st.subheader("📂 Knowledge Base")
    docs = list_documents()
    
    if docs:
        for doc in docs:
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            with col1:
                st.text(doc)
            with col2:
                url = get_presigned_url(doc)
                st.markdown(f"[⬇️]({url})", unsafe_allow_html=True)
            with col3:
                if st.button("🗑️", key=f"del_{doc}", help="Delete file"):
                    delete_document(doc)
                    st.rerun()
    else:
        st.info("No documents found.")

    st.divider()
    col_hist, col_clear = st.columns([0.7, 0.3])
    with col_hist:
        st.subheader("💬 Prompt History")
    with col_clear:
        if st.button("Clear", help="Clear chat history"):
            st.session_state.messages = []
            st.session_state.prompt_history = []
            st.rerun()

    if st.session_state.prompt_history:
        for prompt in reversed(st.session_state.prompt_history[-10:]):
            st.text(f"• {prompt}")
    else:
        st.caption("No queries yet.")

# --- MAIN CHAT INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # PERSISTENT SOURCES
        if "sources" in message:
            st.divider()
            st.caption("📚 **Sources:**")
            for fname in message["sources"]:
                url = get_presigned_url(fname)
                st.markdown(f"- 📄 [{fname}]({url})")

st.chat_input("Ask about your documents...", key="user_input", on_submit=process_input)

# --- PROCESS RESPONSE ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                db = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
                chroma_collection = db.get_or_create_collection(COLLECTION_NAME)
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

                query_engine = index.as_query_engine(similarity_top_k=3)
                response = query_engine.query(st.session_state.messages[-1]["content"])

                st.markdown(response.response)

                # 1. Collect Sources
                source_files = []
                if response.source_nodes:
                    st.divider()
                    st.caption("📚 **Sources:**")
                    seen = set()
                    for node in response.source_nodes:
                        fname = node.metadata.get("filename")
                        if fname and fname not in seen:
                            # Display immediately
                            url = get_presigned_url(fname)
                            st.markdown(f"- 📄 [{fname}]({url})")
                            
                            # Add to list for storage
                            seen.add(fname)
                            source_files.append(fname)

                # 2. Save Response + Sources to History
                st.session_state.messages.append(
                    {
                        "role": "assistant", 
                        "content": response.response,
                        "sources": source_files
                    }
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")
