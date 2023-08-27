import sqlite3
from datetime import date, datetime

from ._database import BaseAdaptiveDatabase, Column, Dtype

_ANOMALY_TABLE_NAME = 'anomaly'


class MachineDatabase(BaseAdaptiveDatabase):
    def __init__(self, directory: str, name: str):
        super().__init__(directory, name)
        self.init_anomaly_table()

    def init_anomaly_table(self):
        if not self.check_table(_ANOMALY_TABLE_NAME):
            self.table_init(table_name=_ANOMALY_TABLE_NAME,
                            columns=[
                                Column(name='time', dtype=Dtype.TIMESTAMP),
                                Column(name='threshold', dtype=Dtype.REAL),
                                Column(name='score', dtype=Dtype.REAL)
                            ])

    def init_stat_table(self, stat_name: str):
        if stat_name == _ANOMALY_TABLE_NAME:
            raise ValueError('Wrong sensor name')

        if not self.check_table(table_name=stat_name):
            self.table_init(table_name=stat_name,
                            columns=[
                                Column(name='time', dtype=Dtype.TIMESTAMP),
                                Column(name='data', dtype=Dtype.REAL)
                            ])

    async def save_stat(self, stat_name: str, data: float, time: datetime = None):
        if time is None:
            time = datetime.now()

        def query(conn):
            cur = conn.cursor()
            cur.execute(f'INSERT INTO {stat_name}(time, data) VALUES (?, ?)',
                        (time, data))

        await self.execute(query)

    async def save_anomaly(self, threshold: float, score: float):
        def query(conn):
            cur = conn.cursor()
            cur.execute(f'INSERT INTO {_ANOMALY_TABLE_NAME}(time, threshold, score) VALUES (?, ?, ?)',
                        (datetime.now(), threshold, score))

        await self.execute(query)

    async def get_stat_by_one_day(self, stat_name: str, t_date: date):
        def query(conn):
            cur = conn.cursor()
            cur.execute(f'SELECT time, data '
                        f'FROM {stat_name} WHERE DATE(time) == ? ORDER BY time',
                        (t_date,))
            return cur.fetchall()

        return await self.execute(query)

    async def get_stat_by_duration(self, stat_name: str, start: date, end: date):
        def query(conn):
            cur = conn.cursor()
            cur.execute(f'SELECT time, data '
                        f'FROM {stat_name} WHERE DATE(time) >= ? and DATE(time) <= ? order by time',
                        (start, end))
            return cur.fetchall()

        return await self.execute(query)

    async def get_stat_avg_of_date(self, stat_name: str, t_date: date):
        def query(conn):
            cur = conn.cursor()
            cur.execute(f'SELECT DATE(time), AVG(data) '
                        f'FROM {stat_name} WHERE DATE(time) == ?',
                        (t_date,))
            return cur.fetchone()[1]

        return await self.execute(query)

    async def get_anomaly_by_one_day(self, t_date: date):
        def query(conn):
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f'SELECT time, threshold, score '
                        f'FROM {_ANOMALY_TABLE_NAME} WHERE DATE(time) == ? ORDER BY time',
                        (t_date,))
            return cur.fetchall()

        return await self.execute(query)

    async def get_anomaly_by_duration(self, start: date, end: date):
        def query(conn):
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f'SELECT time, threshold, score '
                        f'FROM {_ANOMALY_TABLE_NAME} WHERE DATE(time) >= ? and DATE(time) <= ? order by time',
                        (start, end))
            return cur.fetchall()

        return await self.execute(query)
