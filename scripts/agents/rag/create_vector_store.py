# rag_local_json.py
import os
import json
import getpass
from pathlib import Path
from typing import List, TypedDict
from dotenv import load_dotenv
import pickle

import openai
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import START, StateGraph
from sentence_transformers import SentenceTransformer

# =======================
# Config
# =======================
# Directory or file with your JSON data
# Each JSON file can be:
#   A) a list of objects: [{"id": "...", "title": "...", "text": "..."}, ...]
#   B) a single object: {"id": "...", "title": "...", "text": "..."}
DATA_PATH = Path("data/open_f1/drivers_history.json")  # change to your folder OR a single .json file
load_dotenv(override=True)

# Boson/OpenAI-compatible settings
BOSON_API_KEY = os.getenv("BOSON_API_KEY")
BOSON_BASE_URL = "https://hackathon.boson.ai/v1"
CHAT_MODEL = "Qwen3-32B-non-thinking-Hackathon"

# RAG knobs
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 4
TEMPERATURE = 0.2

# =======================
# Load local JSON → Documents
# =======================
def load_json_docs(path: Path) -> List[Document]:
    files = []
    if path.is_dir():
        files = sorted(list(path.rglob("*.json")))
    elif path.is_file() and path.suffix.lower() == ".json":
        files = [path]
    else:
        raise FileNotFoundError(f"No JSON found at {path}")

    docs: List[Document] = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalize into list of dicts
        items = data if isinstance(data, list) else [data]

        for i, item in enumerate(items):
            # Be flexible about field names: prefer "text", else "content", else stringify
            text = (
                item.get("text")
                or item.get("content")
                or json.dumps(item, ensure_ascii=False)
            )
            meta = {
                "source_file": str(fp),
                "idx": i,
                "id": item.get("id"),
                "title": item.get("title"),
            }
            docs.append(Document(page_content=text, metadata=meta))
    return docs

# =======================
# Build the store
# =======================
def build_vector_store(docs: List[Document], embeddings: Embeddings) -> InMemoryVectorStore:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    splits = splitter.split_documents(docs)
    store = InMemoryVectorStore(embeddings)
    _ = store.add_documents(splits)
    return store


class HFEmbeddings(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text], convert_to_numpy=True)[0].tolist()

# =======================
# Main
# =======================
if __name__ == "__main__":
    embeddings = HFEmbeddings()

    # Load local JSON and build index
    base_docs = load_json_docs(DATA_PATH)
    vector_store = build_vector_store(base_docs, embeddings)

    # Save to disk
    with open("data/commentary/vector_store.pkl", "wb") as f:
        pickle.dump(vector_store, f)
    print("Vector store saved!")

