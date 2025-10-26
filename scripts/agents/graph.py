from dotenv import load_dotenv
import os
import time
import base64
import requests
from langgraph.graph import StateGraph, END
import json

from .clone import clone_voice_node
from .llm import intro_bot, F1RacePredictor

# Example run
start = time.time()
load_dotenv()
# BASE_URL = os.getenv("BASE_URL")
# model_name = "Qwen3-32B-non-thinking-Hackathon"
output_dir = "scripts/agents/output/final_audio_clone.wav"



meeting = {
    "meeting_name": "FORMULA 1 SINGAPORE AIRLINES SINGAPORE GRAND PRIX 2024",
    "starting_time": "12:00:00"
}

# Create graph
llm_predictor = F1RacePredictor(meeting)

graph = StateGraph(dict)
# graph.add_node("tts", clone_voice_node)
graph.add_node("llm", llm_predictor.invoke)
# graph.add_edge("llm", "tts")
# graph.add_edge("tts", END)
graph.add_edge("llm", END)
graph.set_entry_point("llm")

app = graph.compile()

# --------------------- Run ---------------------
state = {"commentator_response": []}

with open("data/events_5s_indexed.json", "r", encoding="utf-8") as f:
    drivers = json.load(f)
for i, (driver_id, driver_data) in enumerate(drivers.items()):
    if i > 5:
        break
    try:
        with open("./input/state_store.json", "r", encoding="utf-8") as f:
            state = json.load(f)
    except:
        pass    
    state['latest_events'] = [event['event_description'] for event in driver_data]
    state['output_dir'] = f"scripts/agents/output/audio_{driver_id}.wav"
    state = app.invoke(state)
    with open("scripts/agents/input/state_store.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)
    print(f"success {i}")


# latest_events = [
#     "Position update: Yuki TSUNODA is now P9 at 2024-09-22 12:04:06.63",
#     "Position update: Charles LECLERC is now P8 at 2024-09-22 12:04:06.63",
#     "Overtake event: Charles LECLERC overtook Yuki TSUNODA at 2024-09-22 12:04:06.63"
# ]

# state = {"latest_events": latest_events}

# # x1 = 6 seconds
# # x2 = 8.4 seconds
# # x3 = 13 seconds
# new_text = (
#     # "The Ontarian Grand Prix has just begun, Michael Jordan has a great head start and now is miles ahead of his competition."
#     # "Kobe takes a great start and passes three cards already. We are off with a competitive start."
#     # "This pizza taste really good. I really love pepperoni with goat cheese. What would you like to have dear?"
#     # "I think some red wine would compliment this dish well. How about some Champagne instead?"
#     # "This pizza taste really good. I really love pepperoni with goat cheese. What would you like to have dear?"
#     # "I think some red wine would compliment this dish well. How about some Champagne instead?"
#     # "This pizza taste really good. I really love pepperoni with goat cheese. What would you like to have dear?"
#     # "I think some red wine would compliment this dish well. How about some Champagne instead?"
#     "Leclerc strikes gold on the inside at Turn 4 as he dives past Tsunoda to claim P8. The Ferrari man is now" 
#     "hunting down P7 with precision. Tsunoda fighting hard but losing ground. Next target looks to be the struggling Alpine ahead."
# )

# state = {
#     'new_text': new_text,
#     'output_dir': output_dir,
# }
# result = app.invoke(state)

end = time.time()
print(f"Execution time: {end - start:.2f} seconds")