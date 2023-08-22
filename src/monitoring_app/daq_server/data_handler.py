from datetime import date, datetime, timedelta
from typing import Dict

from config import StatConfig, DBConfig
from util.clock import TimeEvent
from monitoring_app.database import MachineDatabase


class Stat:
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


class Statistics:
    def __init__(self, machine_name, db: MachineDatabase):
        self.machine_name = machine_name

        self.time = TimeEvent()
        self.stats: Dict[str, Stat] = {}
        self.db = db

    async def add_data(self, device_type, data: dict):
        for sensor_name, value in data.items():
            if sensor_name in self.stats:
                self.stats[sensor_name].add(value)
            else:
                self.stats[sensor_name] = Stat(device_type)
                self.db.init_stat_table(sensor_name + DBConfig.HOUR_SUFFIX)
                self.db.init_stat_table(sensor_name + DBConfig.DAY_SUFFIX)
                self.stats[sensor_name].add(value)
        await self.trigger()

    async def trigger(self):
        if self.time.is_day_change():
            await self.save_hour_avg()
            await self.save_day_avg()
        elif self.time.is_hour_change():
            await self.save_hour_avg()

    async def save_day_avg(self):
        last_date = date.today() - timedelta(days=1)
        for sensor_name, stat in self.stats.items():
            day_avg = await self.db.get_stat_avg_of_date(stat_name=sensor_name + DBConfig.HOUR_SUFFIX,
                                                         t_date=last_date)
            await self.db.save_stat(stat_name=sensor_name + DBConfig.DAY_SUFFIX,
                                    data=day_avg,
                                    time=datetime.now() - timedelta(days=1))

    async def save_hour_avg(self):
        for sensor_name, stat in self.stats.items():
            hour_avg = stat.get_average()
            await self.db.save_stat(stat_name=sensor_name + DBConfig.HOUR_SUFFIX,
                                    data=hour_avg,
                                    time=datetime.now() - timedelta(hours=1))


class DataHandler:
    def __init__(self, machine_name):
        self.machine_name = machine_name
        self.db = MachineDatabase(directory=DBConfig.PATH, name=self.machine_name)
        self.statistics = Statistics(self.machine_name, self.db)

    async def save_data(self, machine_event, data: dict):
        if ':' in machine_event:
            del data['time']
            device_type, device_name = machine_event.split(':')
            await self.statistics.add_data(device_type, data)

        else:
            # is anomaly data or something
            pass
