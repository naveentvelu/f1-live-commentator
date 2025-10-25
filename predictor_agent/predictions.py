import os
import openai
from typing import List
from langchain.messages import AnyMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
import operator
from dotenv import load_dotenv

load_dotenv(override=True)
BOSON_API_KEY = os.getenv("BOSON_API_KEY")


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    latest_events: List[str]


class F1RacePredictor:
    def __init__(self, api_key: str = BOSON_API_KEY, base_url: str = "https://hackathon.boson.ai/v1"):
        self.client = openai.Client(api_key=api_key, base_url=base_url)
        self.agent = None

    def build_prompt(self, latest_events: List[str]) -> str:
        return f"""
        You are an expert F1 race commentator providing predictive live commentary.

        Based on the current race data and recent events, predict what's likely to happen in the next 5 minutes, focusing on:

        - Expected position changes
        - Likely overtakes

        Use an engaging, real-time commentary tone—short, vivid, and action-oriented.

        Latest events:
        {latest_events}
        """

    def llm_call(self, state: dict) -> dict:
        """Called automatically by LangGraph."""
        latest_events = state.get("latest_events", [])
        prompt = self.build_prompt(latest_events)

        messages_payload = []
        messages_payload.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model="Qwen3-32B-non-thinking-Hackathon",
            messages=messages_payload,
            temperature=0.7
        )

        return {"messages": [HumanMessage(content=response.choices[0].message.content)]}

    def build_agent(self):
        agent_builder = StateGraph(MessagesState)
        agent_builder.add_node("llm_call", self.llm_call)
        agent_builder.add_edge(START, "llm_call")
        agent_builder.add_edge("llm_call", END)
        self.agent = agent_builder.compile()

    def predict(self, latest_events: List[str]) -> List[HumanMessage]:
        if not self.agent:
            self.build_agent()

        initial_messages = [HumanMessage(content="")] # Placeholder

        state_input = {"messages": initial_messages, "latest_events": latest_events}
        result = self.agent.invoke(state_input)
        return result["messages"]


if __name__ == "__main__":
    latest_events = [
        "Position update: Yuki TSUNODA is now P11",
        "Overtake event: Fernando ALONSO overtook ZHOU Guanyu",
    ]

    predictor = F1RacePredictor()
    predictions = predictor.predict(latest_events)

    for m in predictions:
        print(m.content)
