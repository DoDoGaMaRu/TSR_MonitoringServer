import os
import csv
from typing import List


class CsvWriter:
    def __init__(self, path: str, header: List[str]):
        self._path = path
        self._header = header
        self._file_init()

    def _file_init(self):
        if not os.path.isfile(self._path):
            with open(self._path, "w", newline='\n') as file:
                writer = csv.writer(file)
                writer.writerow(self._header)

    def add_datas(self, datas: List[List]):
        try:
            self._file_init()

            with open(self._path, "a", newline='\n') as file:
                writer = csv.writer(file)
                writer.writerows(datas)

        except Exception as err:
            print('CSV Write Error : \n', err)
