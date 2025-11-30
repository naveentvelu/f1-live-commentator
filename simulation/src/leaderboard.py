from driver import Driver
from pyglet import text

class Leaderboard:

    def __init__(self, ordered_drivers: list[Driver], batch) -> None:
        self.ordered_drivers = ordered_drivers
        self.batch = batch
        self.ts = tuple(text.Label(driver.name_acronym, x=70, y=560 - i * 28, batch=self.batch, font_size=14, color=(0, 0, 0)) for i, driver in enumerate(reversed(self.ordered_drivers)))

    def update(self) -> None:
        self.ts = tuple(text.Label(driver.name_acronym, x=70, y=560 - i * 28, batch=self.batch, font_size=14, color=(0, 0, 0)) for i, driver in enumerate(reversed(self.ordered_drivers)))
