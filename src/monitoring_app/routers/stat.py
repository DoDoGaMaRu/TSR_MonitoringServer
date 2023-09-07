import datetime
import os

from fastapi import APIRouter

from config import DBConfig
from database import MachineDatabase


router = APIRouter(
    prefix="/stat"
)


@router.get("/machineList")
async def get_machine_list():
    res = {}

    files = os.listdir(DBConfig.PATH)
    machine_db_list = [name.replace('.db', '') for name in files if '.db' in name]
    res['machine_list'] = machine_db_list

    return res


@router.get("/hour")
async def get_stat_per_hour(machine: str, date: datetime.date):
    res = {}

    if os.path.isfile(os.path.join(DBConfig.PATH, f'{machine}.db')):
        db = MachineDatabase(directory=DBConfig.PATH, name=machine)
        table_names = [name for name in db.get_table_list() if DBConfig.HOUR_SUFFIX in name]
        for name in table_names:
            res[name] = await db.get_stat_by_one_day(name, date)

    return res


@router.get("/date")
async def get_stat_per_date(machine: str, start: datetime.date, end: datetime.date):
    res = {}

    if os.path.isfile(os.path.join(DBConfig.PATH, f'{machine}.db')):
        db = MachineDatabase(directory=DBConfig.PATH, name=machine)
        table_names = [name for name in db.get_table_list() if DBConfig.DAY_SUFFIX in name]
        for name in table_names:
            res[name] = await db.get_stat_by_duration(name, start, end)

    return res


@router.get("/anomaly")
async def get_anomaly_by_duration(machine: str, start: datetime.date, end: datetime.date):
    res = {}

    if os.path.isfile(os.path.join(DBConfig.PATH, f'{machine}.db')):
        db = MachineDatabase(directory=DBConfig.PATH, name=machine)
        res['anomaly'] = await db.get_anomaly_by_duration(start, end)

    return res
