import socketio

from fastapi import APIRouter


def get_router(sio: socketio.AsyncServer):
    router = APIRouter(
        prefix="/sio"
    )

    @router.get("/machineList")
    async def get_machine_list():
        res = {}
        machine_list = list(sio.namespace_handlers.keys())
        res['machine_list'] = machine_list

        return res

    return router
