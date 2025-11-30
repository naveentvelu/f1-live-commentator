import pyglet
import json
from datetime import datetime
from pyglet import shapes, text
from pyglet.gl import glClearColor

# Create application window with the given width and height
window = pyglet.window.Window(1400, 800)

# Create a batch group for optimized rendering
batch = pyglet.graphics.Batch()

# Set background colour
glClearColor(255, 255, 255, 1)

class Driver:
    __slots__ = ("name_acronym", "team_colour", "driver_number", "x", "y", "position")

    def __init__(self, driver_number: int, name_acronym: str, team_colour: str, x: int, y: int, position: int) -> None:
        self.driver_number = driver_number
        self.name_acronym = name_acronym
        self.x = x
        self.y = y
        self.position = position

        r = int(team_colour[:2], 16)
        g = int(team_colour[2:4], 16)
        b = int(team_colour[4:6], 16)
        self.team_colour = (r,g,b)

# Load drivers
with open('../data/open_f1/drivers.json', 'r') as file:
    drivers = {
        driver["driver_number"]: Driver(driver["driver_number"], driver["name_acronym"], driver["team_colour"], 0, 0, 0)
        for driver in json.load(file)
    }

# Load in racer locations
with open('../data/open_f1/locations.json', 'r') as file:
    locations_data = json.load(file)

# Load in position data
with open('../data/open_f1/positions.json', 'r') as file:
    position_data = json.load(file)

print("Successfully loaded drivers, locations, and position data")

# Convert UTC times to timestamps
for ld in locations_data:
    ld["time"] = datetime.timestamp(datetime.fromisoformat(ld["date"]))

# Sort location data by time, and then driver
locations_data.sort(key=lambda x: (x["time"], x["driver_number"]))

for pd in position_data:
    pd["time"] = datetime.timestamp(datetime.fromisoformat(pd["date"]))

# Sort position data by time, and then driver
position_data.sort(key=lambda x: (x["time"], x["driver_number"]))

# Sample points along the track for rendering
track_location_data = [x for x in locations_data if x["driver_number"] == 1][:800][::4]

# Determine starting index for the simulation
starting_index = 17500

# Resize and position the race within the application window
alpha = 0.08
initial_x = locations_data[starting_index]["x"] * alpha
initial_y = locations_data[starting_index]["y"] * alpha
for ld in locations_data:
    # Rescale x and y coordinates
    ld["x"] = ld["x"] * alpha
    ld["y"] = ld["y"] * alpha

    # Add translational offset
    ld["x"] -= initial_x
    ld["y"] -= initial_y

    ld["x"] += 1250
    ld["y"] += 475

# Define shape of the race track
track_joints = tuple(shapes.Circle(x=track_point["x"], y=track_point["y"], radius=4, color=(0,0,0), batch=batch) for track_point in track_location_data)

track_lines = tuple(shapes.Line(x=track_location_data[i]["x"], y=track_location_data[i]["y"], x2=track_location_data[i+1]["x"], y2=track_location_data[i+1]["y"], thickness=7, color=(0,0,0), batch=batch) for i in range(len(track_location_data)-1))

# Load Formula 1 logo
f1_logo = pyglet.image.load("formula-1-logo-0.png")
f1_sprite = pyglet.sprite.Sprite(f1_logo, x=25, y=520, batch=batch)
f1_sprite.scale = 0.08

# Set up the initial state for the simulation
class SimulationState:
    __slots__ = ("time", "location_index", "position_index", "drivers", "ordered_drivers")

    def __init__(self, drivers, start_time):
        self.time = start_time
        self.location_index = 0
        self.position_index = 0
        self.drivers = drivers

        # Initial positions
        self.drivers[4].position = 1
        self.drivers[1].position = 2
        self.drivers[44].position = 3
        self.drivers[63].position = 4
        self.drivers[81].position = 5
        self.drivers[27].position = 6
        self.drivers[14].position = 7
        self.drivers[22].position = 8
        self.drivers[16].position = 9
        self.drivers[55].position = 10
        self.drivers[23].position = 11
        self.drivers[43].position = 12
        self.drivers[11].position = 13
        self.drivers[20].position = 14
        self.drivers[31].position = 15
        self.drivers[3].position = 16
        self.drivers[18].position = 17
        self.drivers[10].position = 18
        self.drivers[77].position = 19
        self.drivers[24].position = 20

        self.ordered_drivers = sorted(self.drivers.values(), key=lambda driver: driver.position, reverse=True)

start_time = datetime.timestamp(datetime.fromisoformat(locations_data[starting_index]["date"]))

state = SimulationState(drivers, start_time)

## Functions which are ran periodically to create the simulation
def update(dt):
    # Increment elapsed time
    time_acceleration = 2.5
    state.time += time_acceleration * dt

    # "Catch up" on passed events by updating driver locations and positions
    while locations_data[state.location_index]["time"] < state.time:
        ld = locations_data[state.location_index]
        driver = state.drivers[ld["driver_number"]]
        driver.x = ld["x"]
        driver.y = ld["y"]
        state.location_index += 1

    if position_data[state.position_index]["time"] < state.time:
        while position_data[state.position_index]["time"] < state.time:
            pd = position_data[state.position_index]
            driver = state.drivers[pd["driver_number"]]
            driver.position = pd["position"]
            state.position_index += 1

        state.ordered_drivers.sort(key=lambda driver: driver.position, reverse=True)

@window.event
def on_draw():
    # Clear background
    window.clear()

    # Draw track and Formula 1 logo
    batch.draw()

    # Draw drivers
    for driver in state.ordered_drivers:
        driver_icon = shapes.Circle(x=driver.x, y=driver.y, radius=24, color=driver.team_colour)
        driver_name = text.Label(driver.name_acronym, x=driver.x, y=driver.y, anchor_x="center", anchor_y="center")
        driver_icon.draw()
        driver_name.draw()

# Schedule periodic updating of racer locations
pyglet.clock.schedule_interval(update, 1/120)

# Load live commentary generated by the model
commentary = pyglet.media.load("ai_generated_f1_commentary.wav", streaming=False)
commentary.play()

# Start the application
try:
    pyglet.app.run()
except KeyboardInterrupt:
    print()
