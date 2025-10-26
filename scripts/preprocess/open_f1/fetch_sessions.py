import requests, json, os

with open('data/meetings.json', 'r') as file:
        meetings_data = json.load(file)

meeting_key = meetings_data[0]["meeting_key"]

URL = f"https://api.openf1.org/v1/sessions?meeting_key={meeting_key}"

response = requests.get(URL)
data = response.json()

with open("data/sessions.json", "w") as f:
    json.dump(data, f, indent=2)

print("Saved sessions.json")