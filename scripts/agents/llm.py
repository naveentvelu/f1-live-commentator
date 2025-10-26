import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv(override=True)
BOSON_API_KEY = os.getenv("BOSON_API_KEY")
BASE_URL = os.getenv("BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")

def intro_bot(drivers, historical_data):
    system_prompt = """
        You are an expert Formula-1 race commentator providing predictive live commentary for the {self.meeting_name}.
        Based on the driver participants, position and historical facts, provide a starting live commentary in about 
        20 to 50 words.

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
        temperature=0.7,
        max_tokens=128,
    )
    response = llm.invoke(messages)

    # Return as a dict for LangGraph state flow
    return {"predictor_response": [HumanMessage(content=response.content)]}    


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
