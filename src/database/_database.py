import os
import sqlite3
from dataclasses import dataclass
from enum import Enum
from typing import List


class Dtype(Enum):
    TIMESTAMP   = 'TIMESTAMP'
    REAL        = 'REAL'
    TEXT        = 'TEXT'
    INTEGER     = 'INTEGER'


@dataclass
class Column:
    name: str
    dtype: Dtype

    def __post_init__(self):
        if not isinstance(self.name, str) or self.name == 'id':
            raise ValueError("Wrong column name")
        if not isinstance(self.dtype, Dtype):
            raise ValueError("Wrong data type")

    def __str__(self):
        return f'{self.name} {self.dtype.value}'


class BaseDatabase:
    def __init__(self, directory, name):
        self.directory = directory
        self.filename = f'{name}.db'
        self.path = os.path.join(self.directory, self.filename)

        if not os.path.exists(directory):
            os.makedirs(directory)

    def execute_sync(self, func):
        try:
            conn = sqlite3.connect(self.path)
            res = func(conn)
            conn.commit()
            return res
        except Exception as e:
            conn.rollback()
            print(e)
        finally:
            conn.close()

    async def execute(self, func):
        return self.execute_sync(func)

    def check_table(self, table_name: str):
        def query(conn):
            cursor = conn.cursor()
            cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' and name='{table_name}'")
            res = cursor.fetchone()[0]
            if res == 1:
                return True
            else:
                return False

        return self.execute_sync(query)

    def get_table_list(self):
        def query(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return cursor.fetchall()

        res = self.execute_sync(query)
        res = [e[0] for e in res]
        return res


class BaseAdaptiveDatabase(BaseDatabase):
    def table_init(self, table_name, columns: List[Column]):
        columns = ', '.join(map(str, columns))

        def query(conn: sqlite3.Connection):
            conn.execute(f"CREATE TABLE {table_name}(id INTEGER PRIMARY KEY AUTOINCREMENT, {columns})")

        self.execute_sync(query)
