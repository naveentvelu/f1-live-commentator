import requests, json, os
from urllib.request import urlopen

# Meeting and session key
meeting_key = 1246
session_key = 9606

# Load driver data for this meeting and sesssion
with open('../data/drivers.json', 'r') as file:
    drivers_data = json.load(file)

# Get positions for all drivers for this day
total_data = []

for driver_data in drivers_data:
    driver_number = driver_data["driver_number"]
    url = f"https://api.openf1.org/v1/location?session_key={session_key}&meeting_key={meeting_key}&driver_number={driver_number}&date>2024-09-22T12:00:00.000&date<2024-09-22T12:30:00.000"

    response = requests.get(url)
    data = response.json()

    total_data += data

with open("../data/locations.json", "a") as f:
    json.dump(total_data, f, indent=2)

print("Saved locations.json")
