import pyglet
import json
from datetime import datetime
from pyglet import shapes
from pyglet.gl import glClearColor

window = pyglet.window.Window(1400, 800)

batch = pyglet.graphics.Batch()

# Set background colour
glClearColor(255, 255, 255, 1)

# Load drivers
with open('../data/drivers.json', 'r') as file:
    drivers = {driver["driver_number"]: driver for driver in json.load(file)}

for _, driver in drivers.items():
    driver["x"] = 0
    driver["y"] = 0

    # Set driver rgb colour
    r = int(driver["team_colour"][:2], 16)
    g = int(driver["team_colour"][2:4], 16)
    b = int(driver["team_colour"][4:6], 16)
    driver["team_colour_rgb"] = (r,g,b)

# Load in racer locations
with open('../data/locations.json', 'r') as file:
    locations_data = json.load(file)

print("Loaded drivers and locations")

# Convert UTC times to timestamps
for ld in locations_data:
    ld["time"] = datetime.timestamp(datetime.fromisoformat(ld["date"]))

# Sort location data by time, and then driver
locations_data.sort(key=lambda x: (x["time"], x["driver_number"]))

# Set origin to be initial position
alpha_x = 0.05
alpha_y = 0.05

initial_x = locations_data[0]["x"] * alpha_x
initial_y = locations_data[0]["y"] * alpha_y
for ld in locations_data:
    ld["x"] = ld["x"] * alpha_x
    ld["y"] = ld["y"] * alpha_y

    ld["x"] -= initial_x
    ld["y"] -= initial_y

    ld["x"] += 1200
    ld["y"] += 400

class SimulationState:
    def __init__(self, drivers, start_time):
        self.time = start_time
        self.location_index = 0
        self.drivers = drivers

start_time = datetime.timestamp(datetime.fromisoformat(locations_data[0]["date"]))
state = SimulationState(drivers, start_time)

def update(dt):
    time_acceleration = 2.5
    state.time += time_acceleration * dt

    # "Catch up" on passed events by updating driver positions
    while locations_data[state.location_index]["time"] < state.time:
        ld = locations_data[state.location_index]
        driver = state.drivers[ld["driver_number"]]
        driver["x"] = ld["x"]
        driver["y"] = ld["y"]
        state.location_index += 1


@window.event
def on_draw():
    window.clear()
    # Draw driver locations
    rendered_shapes = tuple(shapes.Circle(x=driver["x"], y=driver["y"], radius=20, color=driver["team_colour_rgb"], batch=batch) for index, driver in state.drivers.items())
    batch.draw()

# Scheudle periodic updating of racer locations
pyglet.clock.schedule_interval(update, 0.005)

pyglet.app.run()
