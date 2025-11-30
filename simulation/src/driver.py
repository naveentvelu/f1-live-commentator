from pyglet import shapes, text

class Driver:
    __slots__ = ("name_acronym", "team_colour", "driver_number", "x", "y", "position", "driver_icon", "driver_name")

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

        self.driver_icon = shapes.Circle(x=self.x, y=self.y, radius=24, color=self.team_colour)
        self.driver_name = text.Label(self.name_acronym, x=self.x, y=self.y, anchor_x="center", anchor_y="center")

    def draw(self):
        self.driver_icon.draw()
        self.driver_name.draw()
