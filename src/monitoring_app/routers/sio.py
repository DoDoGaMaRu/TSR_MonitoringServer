import socketio

from fastapi import APIRouter

from config import ServerConfig


def get_router(sio: socketio.AsyncServer):
    router = APIRouter(
        prefix=ServerConfig.SIO_PREFIX
    )

    @router.get("/machineList")
    async def get_machine_list():
        res = {}
        machine_list = [name.replace(ServerConfig.SIO_PREFIX, '') for name in sio.namespace_handlers.keys()]
        res['machine_list'] = machine_list

        return res

    return router
