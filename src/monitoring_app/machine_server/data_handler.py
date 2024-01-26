import os
from typing import Dict, List
from datetime import date, time, datetime, timedelta
from multiprocessing import connection

from config import StatConfig, DBConfig, DataConfig
from util.clock import TimeEvent, get_date, get_time
from database import MachineDatabase
from util.csv_writer import CsvWriter
from util.fcm_sender import FCMSender
from .pipe_serialize import pipe_serialize, MachineThreadEvent, MachineEvent


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


class DataHandler:
    def __init__(self, machine_name: str, w_conn: connection.Connection):
        self.machine_name = machine_name
        self.w_conn = w_conn

        self.save_path = os.path.join(DataConfig.PATH, self.machine_name)
        self.writers: Dict[str, CsvWriter] = {}
        self.time = TimeEvent()

        self.sensors: List[str] = []
        self.stats: Dict[str, Stat] = {}
        self.min_stats: Dict[str, Stat] = {}
        self.db = MachineDatabase(directory=DBConfig.PATH, name=self.machine_name)
        self.fcm_sender = FCMSender()

    def _init_writers(self):
        os.makedirs(self.save_path, exist_ok=True)
        for sensor in self.stats.keys():
            header: List[str] = ['time', 'data']
            path = os.path.join(self.save_path, f'{get_date()}_{sensor}.csv')
            self.writers[sensor] = CsvWriter(path, header)

    async def data_processing(self, machine_event, data: Dict):
        if machine_event == MachineEvent.DataUpdate.name:
            await self._data_update_handle(data)
        elif machine_event == MachineEvent.FaultDetect.name:
            await self._anomaly_handle(data)

    async def _data_update_handle(self, data: Dict):
        if self.time.is_min_change():
            await self._send_min_avg()

            if self.time.is_hour_change():
                await self._save_hour_avg()

                if self.time.is_day_change():
                    await self._save_day_avg()
                    self._init_writers()

                    if self.time.is_month_change():
                        await self._save_month_avg()
                        
                        if self.time.is_year_change():
                            await self._save_year_avg()

        cur_time = get_time()
        for s_name, s_data in data.items():
            if s_name not in self.stats:
                self.db.init_stat_table(s_name + DBConfig.HOUR_SUFFIX)
                self.db.init_stat_table(s_name + DBConfig.DAY_SUFFIX)
                self.db.init_stat_table(s_name + DBConfig.MONTH_SUFFIX)
                self.db.init_stat_table(s_name + DBConfig.YEAR_SUFFIX)
                self.stats[s_name] = Stat(s_data['type'])
                self.min_stats[s_name] = Stat(s_data['type'])
                self._init_writers()
            self.stats[s_name].add(s_data['data'])
            self.min_stats[s_name].add(s_data['data'])

            datas = [[cur_time, data] for data in s_data['data']]
            self.writers[s_name].add_datas(datas)

    async def _anomaly_handle(self, data: Dict):
        self.w_conn.send(
            pipe_serialize(
                event=MachineThreadEvent.DATA_UPDATE,
                machine_name=self.machine_name,
                machine_event=MachineEvent.FaultDetect,
                data=data
            )
        )
        score = data["score"]
        threshold = data["threshold"]

        if score > threshold:
            await self.db.save_anomaly(score=score, threshold=threshold)
            await self.fcm_sender.send(
                topic='anomaly',
                title=f'{self.machine_name} 이상치 감지',
                body=f'상세 정보 : {score}/{threshold}'
            )

    async def _send_min_avg(self):
        cur_time = datetime.now()
        for s_name, s_stat in self.min_stats.items():
            data = {
                'sensor_name': s_name,
                'data': s_stat.get_average(),
                'time': str(cur_time)
            }
            self.w_conn.send(
                pipe_serialize(
                    event=MachineThreadEvent.DATA_UPDATE,
                    machine_name=self.machine_name,
                    machine_event=MachineEvent.DataUpdate,
                    data=data
                )
            )

    async def _save_hour_avg(self):
        for sensor_name, stat in self.stats.items():
            hour_avg = stat.get_average()
            await self.db.save_stat(
                stat_name=sensor_name + DBConfig.HOUR_SUFFIX,
                data=hour_avg,
                time=(datetime.now()-timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            )

    async def _save_day_avg(self):
        cur_date = datetime.combine(date=date.today(), time=time())
        last_date = cur_date-timedelta(days=1)
        for sensor_name, stat in self.stats.items():
            day_avg = await self.db.get_stat_avg(
                stat_name=sensor_name + DBConfig.HOUR_SUFFIX,
                start=last_date,
                end=cur_date
            )
            await self.db.save_stat(
                stat_name=sensor_name + DBConfig.DAY_SUFFIX,
                data=day_avg,
                time=last_date
            )

    async def _save_month_avg(self):
        cur_month = datetime.combine(date=date.today(), time=time()).replace(day=1)
        last_month = (cur_month-timedelta(days=1)).replace(day=1)
        for sensor_name, stat in self.stats.items():
            month_avg = await self.db.get_stat_avg(
                stat_name=sensor_name + DBConfig.DAY_SUFFIX,
                start=last_month,
                end=cur_month
            )
            await self.db.save_stat(
                stat_name=sensor_name + DBConfig.MONTH_SUFFIX,
                data=month_avg,
                time=last_month
            )

    async def _save_year_avg(self):
        cur_year = datetime.combine(date=date.today(), time=time()).replace(month=1, day=1)
        last_year = (cur_year-timedelta(days=1)).replace(month=1, day=1)
        for sensor_name, stat in self.stats.items():
            year_avg = await self.db.get_stat_avg(
                stat_name=sensor_name + DBConfig.MONTH_SUFFIX,
                start=last_year,
                end=cur_year
            )
            await self.db.save_stat(
                stat_name=sensor_name + DBConfig.YEAR_SUFFIX,
                data=year_avg,
                time=last_year
            )
