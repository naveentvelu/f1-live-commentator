# rag_local_json.py
import os
import json
import getpass
from pathlib import Path
from typing import List, TypedDict

import openai
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import START, StateGraph

# =======================
# Config
# =======================
# Directory or file with your JSON data
# Each JSON file can be:
#   A) a list of objects: [{"id": "...", "title": "...", "text": "..."}, ...]
#   B) a single object: {"id": "...", "title": "...", "text": "..."}
DATA_PATH = Path("./data")  # change to your folder OR a single .json file

# Boson/OpenAI-compatible settings
BOSON_API_KEY = os.getenv("BOSON_API_KEY") or getpass.getpass("Enter Boson AI API key: ")
BOSON_BASE_URL = "https://hackathon.boson.ai/v1"
CHAT_MODEL = "gpt-4o-mini"          # adjust if needed
EMBED_MODEL = "text-embedding-3-small"

# RAG knobs
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 4
TEMPERATURE = 0.2

# =======================
# Minimal Boson wrappers
# =======================
class BosonChatModel:
    """Minimal wrapper to make Boson chat API behave like a simple LangChain LLM."""
    def __init__(self, apikey: str, model: str = CHAT_MODEL, base_url: str = BOSON_BASE_URL):
        self.client = openai.Client(api_key=apikey, base_url=base_url)
        self.model = model

    def _to_boson_messages(self, messages: List[BaseMessage]):
        boson = []
        for m in messages:
            role = "user" if m.type == "human" else "assistant"
            boson.append({"role": role, "content": m.content})
        return boson

    def invoke(self, messages: List[BaseMessage], temperature: float = TEMPERATURE) -> AIMessage:
        # Accepts a list of LangChain BaseMessage (e.g., from a ChatPrompt)
        boson_messages = self._to_boson_messages(messages)
        resp = self.client.chat.completions.create(
            model=self.model, messages=boson_messages, temperature=temperature
        )
        return AIMessage(content=resp.choices[0].message.content)

class BosonEmbeddings(Embeddings):
    def __init__(self, apikey: str, model: str = EMBED_MODEL, base_url: str = BOSON_BASE_URL):
        self.client = openai.Client(api_key=apikey, base_url=base_url)
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Simple loop; for large corpora, batch calls if your endpoint supports it.
        out = []
        for t in texts:
            e = self.client.embeddings.create(model=self.model, input=t).data[0].embedding
            out.append(e)
        return out

    def embed_query(self, text: str) -> List[float]:
        return self.client.embeddings.create(model=self.model, input=text).data[0].embedding

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

# =======================
# Prompt + Graph
# =======================
PROMPT = ChatPromptTemplate.from_template(
"""You are a helpful AI assistant answering questions strictly from the given context.
If the answer cannot be found in context, say you do not have enough information.

Context:
{context}

Question:
{question}

Answer concisely and cite the source_file and title for each fact you use."""
)

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

def make_rag_app(vector_store: InMemoryVectorStore, llm: BosonChatModel):
    def retrieve(state: State):
        retrieved = vector_store.similarity_search(state["question"], k=TOP_K)
        return {"context": retrieved}

    def generate(state: State):
        def cite(doc: Document):
            src = doc.metadata.get("source_file", "unknown")
            title = doc.metadata.get("title") or "untitled"
            return f"[{title}]({src})"
        ctx = "\n\n".join(
            f"{doc.page_content}\n(Citation: {cite(doc)})" for doc in state["context"]
        )
        messages = PROMPT.format_messages(question=state["question"], context=ctx)
        response = llm.invoke(messages)
        return {"answer": response.content}

    g = StateGraph(State)
    g.add_node("retrieve", retrieve)
    g.add_node("generate", generate)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "generate")
    return g.compile()

# =======================
# Main
# =======================
if __name__ == "__main__":
    # Init models
    llm = BosonChatModel(apikey=BOSON_API_KEY, model=CHAT_MODEL)
    embeddings = BosonEmbeddings(apikey=BOSON_API_KEY, model=EMBED_MODEL)

    # Load local JSON and build index
    base_docs = load_json_docs(DATA_PATH)
    vector_store = build_vector_store(base_docs, embeddings)

    # Build RAG pipeline
    graph = make_rag_app(vector_store, llm)

    # Example query
    q = "What are the key takeaways in this corpus?"
    result = graph.invoke({"question": q})
    print("\n=== ANSWER ===\n")
    print(result["answer"])
