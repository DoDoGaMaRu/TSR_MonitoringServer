import datetime

from fastapi import APIRouter


router = APIRouter(
    prefix="/stat"
)


@router.get("/machineList")
async def get_machine_list():
    pass


@router.get("/hour")
async def get_stat_per_hour(machine_name: str, date: datetime.date):
    return [machine_name, date]


@router.get("/date")
async def get_stat_per_date(machine_name: str, start: datetime.date, end: datetime.date):
    return [machine_name, start, end]


@router.get("/anomaly")
async def get_anomaly_by_duration(machine_name: str, start: datetime.date, end: datetime.date):
    return [machine_name, start, end]
