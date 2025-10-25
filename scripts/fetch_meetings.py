import requests, json, os

URL = f"https://api.openf1.org/v1/meetings?year=2024&country_name=Singapore"

response = requests.get(URL)
data = response.json()

# Check if data folder exists
os.makedirs("data", exist_ok=True)

with open("data/meetings.json", "w") as f:
    json.dump(data, f, indent=2)

print("Saved meetings.json")