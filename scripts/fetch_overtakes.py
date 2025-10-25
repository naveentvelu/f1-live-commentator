import requests, json, os

with open('data/sessions.json', 'r') as file:
        sessions_data = json.load(file)

# Get the race session key
for s_data in sessions_data:
    if s_data["session_type"] == "Race":
        meeting_key = s_data["meeting_key"]
        session_key = s_data["session_key"]
        date_start = s_data["date_start"]

URL = f"https://api.openf1.org/v1/overtakes?meeting_key={meeting_key}&session_key={session_key}&date>={date_start}"

response = requests.get(URL)
data = response.json()

print(f"Total data: {len(data)}")

with open("data/overtakes.json", "w") as f:
    json.dump(data, f, indent=2)

print("Saved overtakes.json")