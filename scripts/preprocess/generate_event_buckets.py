import json
from datetime import datetime, timedelta
from dateutil import parser

class F1RaceSimulator:
    def __init__(self, data_paths, driver_path):
        self.data_paths = data_paths
        self.driver_path = driver_path
        self.data = []
        self.driver_map = {}

    def clean_data(self, data, label):
        clean_data = []
        for d in data:
            date_field = "date_start" if label == "lap" else "date"
            date_value = d.get(date_field)
            if not date_value:
                continue
            clean_data.append(d)
        return clean_data

    def load_and_label(self, path, label):
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
        with open(self.driver_path, "r") as f:
            drivers = json.load(f)
        self.driver_map = {d["driver_number"]: d["full_name"] for d in drivers}

    def load_all_data(self):
        for label, path in self.data_paths.items():
            self.data += self.load_and_label(path, label)
        self.data.sort(key=lambda x: x['event_time'])
        print(f"Total events loaded: {len(self.data)}")

    def stream_indexed(self, output_file="events_indexed.json", interval_sec=5):
        """
        Aggregate events in fixed time intervals (default 5 seconds) 
        and write to JSON.
        """
        if not self.data:
            print("No data loaded.")
            return

        # Determine the start and end times
        start_time = self.data[0]['event_time']
        end_time = self.data[-1]['event_time']
        current_time = start_time

        indexed_events = {}

        while current_time <= end_time:
            next_time = current_time + timedelta(seconds=interval_sec)
            # Find events in this interval
            events_in_interval = []
            while self.data and self.data[0]['event_time'] < next_time:
                event = self.data.pop(0)
                driver_name = self.driver_map.get(event.get('driver_number'), "Unknown Driver")
                event_copy = event.copy()
                
                if event['event_type'] == "lap":
                    event_copy['driver_name'] = driver_name
                    event_copy['event_description'] = f"Lap event: {driver_name} completed a lap in {event_copy['lap_duration']} seconds"
                elif event['event_type'] == "position":
                    event_copy['driver_name'] = driver_name
                    event_copy['event_description'] = f"Position update: {driver_name} is now P{event['position']}"
                elif event['event_type'] == "pit_stop":
                    event_copy['driver_name'] = driver_name
                    event_copy['event_description'] = f"Pit stop: {driver_name}"
                elif event['event_type'] == "overtake":
                    overtaking_driver_name = self.driver_map.get(event.get('overtaking_driver_number'), "Unknown Driver")
                    overtaken_driver_name = self.driver_map.get(event.get('overtaken_driver_number'), "Unknown Driver")
                    event_copy['overtaking_driver_name'] = overtaking_driver_name
                    event_copy['overtaken_driver_name'] = overtaken_driver_name
                    event_copy['event_description'] = f"Overtake event: {overtaking_driver_name} overtook {overtaken_driver_name}"
                
                # Remove datetime object before JSON serialization
                event_copy['event_time'] = event_copy['event_time'].isoformat()
                events_in_interval.append(event_copy)
            indexed_events[current_time.isoformat()] = events_in_interval
            current_time = next_time

        # Write to JSON
        with open(output_file, "w") as f:
            json.dump(indexed_events, f, indent=2)

        print(f"Events written to {output_file}")

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

    simulator = F1RaceSimulator(data_paths, driver_path)
    simulator.load_drivers()
    simulator.load_all_data()
    simulator.stream_indexed(output_file="data/events_5s_indexed.json", interval_sec=5)
