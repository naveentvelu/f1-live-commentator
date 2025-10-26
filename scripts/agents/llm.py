import os
import json
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

import os
import json
import getpass
from pathlib import Path
from typing import List, TypedDict
import pickle
import openai
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import START, StateGraph

load_dotenv(override=True)
BOSON_API_KEY = os.getenv("BOSON_API_KEY")
BOSON_BASE_URL = "https://hackathon.boson.ai/v1"
BASE_URL = BOSON_BASE_URL
LLM_MODEL = os.getenv("LLM_MODEL")

# RAG knobs
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 4
TEMPERATURE = 0.2

class BosonChatModel:
    """Minimal wrapper to make Boson chat API behave like a simple LangChain LLM."""
    def __init__(self, apikey: str, model: str = LLM_MODEL, base_url: str = BOSON_BASE_URL):
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

PROMPT = ChatPromptTemplate.from_template(
"""You are a helpful AI assistant answering questions strictly from the given context.
If the answer cannot be found in context, say you do not have enough information.

Context:
{context}

Question:
{question}

Remove the Source file citing.
Remove any information before August 2024."""
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

class HFEmbeddings(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text], convert_to_numpy=True)[0].tolist()

def intro_bot():

    llm = BosonChatModel(apikey=BOSON_API_KEY)

    # Save to disk
    with open("vector_store.pkl", "rb") as f:
        vector_store = pickle.load(f)

    # Build RAG pipeline
    graph = make_rag_app(vector_store, llm)

    # Query
    q = """You are delivering the opening remarks for the 2024 Singapore Grand Prix. 
    Using the corpus, extract key insights on: top drivers, team performance, recent milestones, and notable Singapore circuit context. 
    Summarize as a concise introduction."""
    result = graph.invoke({"question": q})
    historical_data = result['answer']

    drivers = []
    with open("data/drivers.json", "r") as f:
        drivers_data = json.load(f)
    
    for d in drivers_data:
        drivers.append(d['full_name'])
    

    system_prompt = """
        You are an expert Formula-1 race commentator providing predictive live commentary for the {self.meeting_name}.
        Based on the driver participants, position and historical facts, provide a starting live commentary in about 
        50 to 100 words.

        Example:
        The turkish Grand Prix, is underway. Verstappen starting at p4, with Leclerc at p8. They
        are the favorites to win this race according to statistics from STATS F1. Steven on the other hand,
        is a dark horse and should not be overlooked. Previous winner of this Grand Prix was Norris. Sharing
        the stage with Verstappen and Leclerc.

        Notes:
        - Use an engaging, real-time commentary tone—short, vivid, and action-oriented.
        - Avoid descriptive phrases and keep commentaries precise.
        - Do not return nothing.
        - Avoid punctuations other than ',' and '.'
        - Assume that this is the start of the commentary and will have follow up commentary after.
    """
    human_prompt = f"""
        Driver participants:
        {drivers}

        Historical data:
        {historical_data}
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=BOSON_API_KEY,
        base_url=BASE_URL,
        temperature=0.8
    )
    response = llm.invoke(messages)
    # print(response)

    # Return as a dict for LangGraph state flow
    return {"commentator_response": [response.content]}


# if __name__ == "__main__":
#     intro_bot()

class F1RacePredictor:
    def __init__(self, meeting: dict):
        # Use LangChain's ChatOpenAI wrapper (not openai.Client)
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=BOSON_API_KEY,
            base_url=BASE_URL,
            temperature=0.8,
            max_tokens=256,
        )
        self.starting_time = meeting['starting_time']
        self.meeting_name = meeting['meeting_name']
        self.system_prompt = self._init_system_prompt()
    
    def _init_system_prompt(self) -> str:
        return f"""
        You are an expert Formula-1 race commentator providing predictive live commentary for the {self.meeting_name}
        starting at {self.starting_time}.
        Based on the current race data and recent events, provide live commentary in about 20 to 50 words.
        Only if there are not many events, predict what's likely to happen next, focusing on key
        events like expected position changes and likely overtakes.

        Example:
        The turkish Grand Prix, its lights out and away we go. Hamilton though takes a very good start, passes two cars already.
        Stroll is on the lead taking a turn one ahead of his teammate. Princeton slowly catching up to Stroll.
        Notes:
        - Use an engaging, real-time commentary tone—short, vivid, and action-oriented.
        - Avoid wordy phrases and keep commentaries precise.
        - Do not return nothing.
        - Avoid punctuations other than , and .
        - Assume that there are commentary before and after the message.
        - If Latest race events is missing, predict what will happen next.
        """

    def event_prompt(self, state) -> str:
        return f"""
            Latest race events:\n{chr(10).join(state["latest_events"])}
            Continue the commentary below in 20 to 50 words.
            {state['commentator_response']}
            """

    def invoke(self, state: dict) -> dict:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=self.event_prompt(state)),
        ]

        # Invoke the LangChain LLM (synchronous call)
        response = self.llm.invoke(messages)
        # state['commentator_response'] = [HumanMessage(content=response.content)]
        state['commentator_response'].append(response.content)
        # Return as a dict for LangGraph state flow
        return state


# if __name__ == "__main__":
#     meeting = {
#         "meeting_name": "FORMULA 1 SINGAPORE AIRLINES SINGAPORE GRAND PRIX 2024",
#         "starting_time": "12:00:00"
#     }
#     latest_events = [
#         "Position update: Yuki TSUNODA is now P9 at 2024-09-22 12:04:06.63",
#         "Position update: Charles LECLERC is now P8 at 2024-09-22 12:04:06.63",
#         "Overtake event: Charles LECLERC overtook Yuki TSUNODA at 2024-09-22 12:04:06.63"
#     ]
    
#     state = {"latest_events": latest_events}
#     predictor = F1RacePredictor(meeting)
#     predictions = predictor.invoke(state)["predictor_response"]

#     print("\n🏁 Start of output:")
#     for m in predictions:
#         print(m.content)
