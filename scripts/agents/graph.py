from dotenv import load_dotenv
import os
import time
import base64
import requests
from langgraph.graph import StateGraph, END
import json

from .commentary import clone_voice_node, intro_bot, F1RacePredictor, HFEmbeddings


start = time.time()
load_dotenv()

meeting = {
    "meeting_name": "FORMULA 1 SINGAPORE AIRLINES SINGAPORE GRAND PRIX 2024",
    "starting_time": "12:00:00"
}

# Create graph
llm_predictor = F1RacePredictor(meeting)

graph = StateGraph(dict)
graph.add_node("tts", clone_voice_node)
graph.add_node("llm", llm_predictor.invoke)
graph.add_edge("llm", "tts")
graph.add_edge("tts", END)
graph.add_edge("llm", END)
graph.set_entry_point("llm")

app = graph.compile()

# --------------------- Run ---------------------
state_store_path = "data/commentary/input/state_store.json"
state = intro_bot()
with open("data/open_f1/events_5s_indexed.json", "r", encoding="utf-8") as f:
    drivers = json.load(f)
for i, (time_stamp, driver_data) in enumerate(drivers.items()):
    if i % 3 == 0:
        print(time_stamp)
    if i > 11:
        break
    try:
        with open(state_store_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except:
        pass    
    state['latest_events'] = [event['event_description'] for event in driver_data]
    state['output_dir'] = f"scripts/agents/output/audio_{time_stamp}.wav"
    state = app.invoke(state)
    with open(state_store_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)

end = time.time()
print(f"Execution time: {end - start:.2f} seconds")