import asyncio
import uvicorn
import logging
import socketio

from typing import Tuple
from uvicorn import Config, Server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from util import logger
from config import ServerConfig, LoggerConfig

from .routers import get_sio_router, stat_router
from .machine_server import Runner, MachineEvent, EventHandler
from .custom_namespace import CustomNamespace


class MachineHandler(EventHandler):
    def __init__(self, sio, machine_logger, sio_logger):
        self.sio = sio
        self.machine_logger = machine_logger
        self.sio_logger = sio_logger

    async def __call__(self, machine_event: MachineEvent, machine_name: str, machine_msg: Tuple[str, object]):
        if machine_name is not None:
            namespace = f'{ServerConfig.SIO_PREFIX}/{machine_name}'

            if machine_event == MachineEvent.MESSAGE:
                event, data = machine_msg
                await self.sio.emit(namespace=namespace, event=event, data=data)

            elif machine_event == MachineEvent.CONNECT:
                machine_namespace = CustomNamespace(namespace=namespace, logger=self.sio_logger)
                self.sio.register_namespace(namespace_handler=machine_namespace)
                self.machine_logger.info(f'{machine_name} connected')

            elif machine_event == MachineEvent.DISCONNECT:
                del self.sio.namespace_handlers[namespace]
                self.machine_logger.info(f'{machine_name} disconnected')


class MonitoringApp:
    def __init__(self):
        self.host = ServerConfig.HOST
        self.port = ServerConfig.PORT
        self.app = FastAPI()
        self.app.add_middleware(CORSMiddleware,
                                allow_origins=ServerConfig.CORS_ORIGINS,
                                allow_credentials=True,
                                allow_methods=['*'],
                                allow_headers=['*'],)
        self.sio = socketio.AsyncServer(async_mode='asgi',
                                        cors_allowed_origins='*',)
        self.loop = asyncio.get_event_loop()

        self._set_logger()
        self._configure_event()
        self._configure_routes()

        self.machine_server_runner = Runner(host=self.host,
                                            port=ServerConfig.TCP_PORT,
                                            event_handler=MachineHandler(self.sio, self.machine_logger, self.sio_logger))

    def _server_load(self) -> Server:
        uvicorn_log_config = uvicorn.config.LOGGING_CONFIG
        uvicorn_log_config['formatters']['access']['fmt'] = LoggerConfig.FORMAT
        uvicorn_log_config["formatters"]["default"]["fmt"] = LoggerConfig.FORMAT

        socket_app = socketio.ASGIApp(self.sio, self.app)
        config = Config(app=socket_app,
                        host=self.host,
                        port=self.port,
                        loop=self.loop)
        return Server(config)

    def _set_logger(self):
        self.machine_logger = logger.get_logger(name='machine', log_level=logging.INFO, save_path=LoggerConfig.PATH)
        self.sio_logger = logger.get_logger(name='sio.access', log_level=logging.INFO, save_path=LoggerConfig.PATH)

    def _configure_event(self):
        @self.app.on_event("startup")
        async def startup_event():
            uvicorn_error = logging.getLogger('uvicorn.error')
            uvicorn_access = logging.getLogger('uvicorn.access')
            uvicorn_error.setLevel(logging.ERROR)

            formatter = logging.Formatter(LoggerConfig.FORMAT)
            uvicorn_error.addHandler(logger.get_file_handler(path=LoggerConfig.PATH,
                                                             name=uvicorn_error.name,
                                                             formatter=formatter))
            uvicorn_access.addHandler(logger.get_file_handler(path=LoggerConfig.PATH,
                                                              name=uvicorn_access.name,
                                                              formatter=formatter))

    def _configure_routes(self):
        sio_router = get_sio_router(self.sio)

        self.app.include_router(sio_router)
        self.app.include_router(stat_router)

    def run(self):
        try:
            self.loop = asyncio.get_event_loop()
            web_server = self._server_load()

            self.machine_server_runner.run()
            self.loop.run_until_complete(web_server.serve())

            self.machine_server_runner.join()
        except Exception as e:
            print(f"An error occurred: {e}")
