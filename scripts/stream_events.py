import json
from datetime import datetime
from dateutil import parser
import time

class F1RaceSimulator:
    def __init__(self, data_paths, driver_path, time_scale=1):
        """
        data_paths: dict with keys 'position', 'lap', 'pit' pointing to JSON file paths
        driver_path: path to drivers.json
        time_scale: speed-up factor for demo
        """
        self.data_paths = data_paths
        self.driver_path = driver_path
        self.time_scale = time_scale
        self.data = []
        self.driver_map = {}
    
    def clean_data(self, data, label):
        """Filter out records with missing or invalid date fields"""
        clean_data = []
        for d in data:
            date_field = "date_start" if label == "lap" else "date"
            date_value = d.get(date_field)
            if not date_value:
                continue
            clean_data.append(d)
        return clean_data

    def load_and_label(self, path, label):
        """Load JSON data, clean it, and label events with type and parsed event_time"""
        print(f"Reading from {path} for {label}")
        with open(path) as f:
            data = json.load(f)
        data = self.clean_data(data, label)
        for d in data:
            d['event_type'] = label
            date_field = "date_start" if label == "lap" else "date"
            d['event_time'] = parser.parse(d[date_field])
        return data

    def load_drivers(self):
        """Load driver mapping from number to full name"""
        with open(self.driver_path, "r") as f:
            drivers = json.load(f)
        self.driver_map = {d["driver_number"]: d["full_name"] for d in drivers}

    def load_all_data(self):
        """Load and merge all endpoints into a unified, sorted timeline"""
        for label, path in self.data_paths.items():
            self.data += self.load_and_label(path, label)
        self.data.sort(key=lambda x: x['event_time'])
        print(f"Total events loaded: {len(self.data)}")

    def stream(self):
        """Simulate the race events in chronological order"""
        for i in range(len(self.data)):
            event = self.data[i]
            driver_name = self.driver_map.get(event.get('driver_number'), "Unknown Driver")
            
            # Display event
            if event['event_type'] == "lap":
                print(f"Lap event: {driver_name} completed a lap at {event['event_time']}")
            elif event['event_type'] == "position":
                print(f"Position update: {driver_name} is now P{event['position']} at {event['event_time']}")
            elif event['event_type'] == "pit_stop":
                print(f"Pit stop: {driver_name} at {event['event_time']}")
            elif event['event_type'] == "overtake":
                overtaking_driver_name = self.driver_map.get(event.get('overtaking_driver_number'), "Unknown Driver")
                overtaken_driver_name = self.driver_map.get(event.get('overtaken_driver_number'), "Unknown Driver")
                print(f"Overtake event: {overtaking_driver_name} overtook {overtaken_driver_name} at {event['event_time']}")
            
            # Compute wait time until next event
            if i < len(self.data) - 1:
                delta = (self.data[i+1]['event_time'] - event['event_time']).total_seconds() / self.time_scale
                time.sleep(max(0.1, delta))  # minimum pause for demo

# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    data_paths = {
        "position": "data/positions.json",
        "lap": "data/laps.json",
        "pit": "data/pit_stops.json",
        "overtake": "data/overtakes.json"
    }
    driver_path = "data/drivers.json"

    simulator = F1RaceSimulator(data_paths, driver_path, time_scale=1000)
    simulator.load_drivers()
    simulator.load_all_data()
    simulator.stream()
