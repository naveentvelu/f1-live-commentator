from driver import Driver

class SimulationState:
    __slots__ = ("time", "location_index", "position_index", "interval_index", "lap_index", "drivers", "ordered_drivers")

    def __init__(self, drivers: dict[int, Driver], start_time: int) -> None:
        self.time = start_time
        self.location_index = 0
        self.position_index = 0
        self.interval_index = 0
        self.lap_index = 0
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
