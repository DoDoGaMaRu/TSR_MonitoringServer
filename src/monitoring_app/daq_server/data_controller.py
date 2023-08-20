from datetime import date, timedelta
from typing import Dict

from config import StatConfig
from util.clock import TimeChecker


class Statistics:
    def __init__(self, sensor_type):
        self.mode = StatConfig.MODE[sensor_type]
        self.data_sum = 0
        self.size = 0

    def add(self, data):
        self.data_sum += sum(self.mode(data))
        self.size += len(data)

    def reset(self):
        self.data_sum = 0
        self.size = 0

    def get_average(self):
        average = self.data_sum / self.size
        self.reset()
        return average


class DataController:
    def __init__(self, machine_name):
        self.machine_name = machine_name

        self.time = TimeChecker()
        self.stats: Dict[str, Statistics] = {}
        # self.db = Database(name=self.machine_name)

    async def add_data(self, machine_event, data: dict):
        await self.trigger()

        del data['time']
        device_type, device_name = machine_event.split(':')

        for sensor_name, value in data.items():
            if sensor_name not in self.stats:
                self.stats[sensor_name] = Statistics(device_type)
            self.stats[sensor_name].add(value)

    async def trigger(self):
        if self.time.is_day_change():
            await self.save_day_avg()
            await self.save_hour_avg()
        elif self.time.is_hour_change():
            await self.save_hour_avg()

    async def save_day_avg(self):
        pass

    async def save_hour_avg(self):
        for sensor_name, stat in self.stats.items():
            hour_avg = stat.get_average()
            print(hour_avg)
