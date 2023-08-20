import socketio

from fastapi import APIRouter


def get_router(sio: socketio.AsyncServer):
    router = APIRouter(
        prefix="/sio"
    )

    @router.get("/machineList")
    async def get_machine_list():
        machine_list = list(sio.namespace_handlers.keys())
        return machine_list

    return router
