from driver import Driver
from pyglet import text, shapes

class Leaderboard:

    def __init__(self, ordered_drivers: list[Driver], final_lap: int, batch) -> None:
        self.ordered_drivers = ordered_drivers
        self.batch = batch
        self.lap = 1
        self.final_lap = final_lap

        self.lap_title = text.Label(f"LAP {self.lap}/{self.final_lap}", x=180, y=595, batch=self.batch, font_size=16, color=(0, 0, 0), anchor_x="center")
        self.boxes = tuple(shapes.Rectangle(70, 555 - i * 28, 220, 26, color=driver.team_colour+(220,), batch=self.batch) for i, driver in enumerate(reversed(self.ordered_drivers)))
        self.ps = tuple(text.Label(str(i+1), x=90, y=560 - i * 28, batch=self.batch, font_size=14, color=(255, 255, 255), anchor_x="center") for i, driver in enumerate(reversed(self.ordered_drivers)))
        self.ts = tuple(text.Label(driver.name_acronym, x=120, y=560 - i * 28, batch=self.batch, font_size=14, color=(255, 255, 255)) for i, driver in enumerate(reversed(self.ordered_drivers)))
        #self.ints = tuple(text.Label(driver.gap_to_leader, x=220, y=560 - i * 28, batch=self.batch, font_size=14, color=(255, 255, 255), anchor_x="center") for i, driver in enumerate(reversed(self.ordered_drivers)))

    def update(self) -> None:
        self.boxes = tuple(shapes.Rectangle(70, 555 - i * 28, 220, 26, color=driver.team_colour+(220,), batch=self.batch) for i, driver in enumerate(reversed(self.ordered_drivers)))
        self.ts = tuple(text.Label(driver.name_acronym, x=120, y=560 - i * 28, batch=self.batch, font_size=14, color=(255, 255, 255)) for i, driver in enumerate(reversed(self.ordered_drivers)))
        #self.ints = tuple(text.Label(driver.gap_to_leader, x=220, y=560 - i * 28, batch=self.batch, font_size=14, color=(255, 255, 255), anchor_x="center") for i, driver in enumerate(reversed(self.ordered_drivers)))
        self.lap_title = text.Label(f"LAP {self.lap}/{self.final_lap}", x=180, y=595, batch=self.batch, font_size=16, color=(0, 0, 0), anchor_x="center")
