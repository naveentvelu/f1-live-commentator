import json
from datetime import datetime
from dateutil import parser
import time

def clean_data(data, label):
    clean_data = []
    for d in data:
        # Determine which date field to use
        date_field = "date_start" if label == "lap" else "date"
        date_value = d.get(date_field)
        # Skip records with missing or invalid date
        if not date_value:
            continue
        clean_data.append(d)
    return clean_data

def load_and_label(path, label):
    print(f"Reading data from {path} for {label}")
    with open(path) as f:
        data = json.load(f)
    data = clean_data(data, label)
    for d in data:
        d['event_type'] = label
        if label == "lap":
            d['event_time'] = parser.parse(d['date_start'])
        else:
            d['event_time'] = parser.parse(d['date'])
    return data

data = []
data += load_and_label("data/positions.json", "position")
data += load_and_label("data/laps.json", "lap")
data += load_and_label("data/pit_stops.json", "pit")

# Sort everything chronologically
data.sort(key=lambda x: x['event_time'])

print(f"Total events : {len(data)}")

# Create driver number to name mapping
with open("data/drivers.json", "r") as f:
    drivers = json.load(f)

driver_mp = {}
for driver in drivers:
    driver_num = driver["driver_number"]
    driver_name = driver["full_name"]
    driver_mp[driver_num] = driver_name


# Start streaming
time_scale = 1
for i in range(len(data)):
    print(i)
    event = data[i]
    driver_name= driver_mp[event['driver_number']]
    
    # Display event
    if event['event_type'] == "lap":
        print(f"Lap event: {driver_name} completed a lap at {event['event_time']}")
    elif event['event_type'] == "position":
        print(f"Position update: {driver_name} is now P{event['position']} at {event['event_time']}")
    elif event['event_type'] == "pit_stop":
        print(f"Pit stop: {driver_name} at {event['event_time']}")

    # Compute wait time until next event
    if i < len(data) - 1:
        delta = (data[i+1]['event_time'] - event['event_time']).total_seconds() / time_scale
        time.sleep(max(0.1, delta))  # minimum 0.1s pause for demo

