import asyncio
import socketio

from network.tcp_server import TCPServer
from multiprocessing import Pipe
from fastapi import FastAPI
from uvicorn import Config, Server
from socketio import AsyncNamespace

from config import TcpServerConfig, TcpEventConfig
from network.protocols import recv_protocol


class CustomNamespace(AsyncNamespace):
    def __init__(self, namespace):
        super().__init__(namespace=namespace)
        self.name = namespace[1:]

    def on_connect(self, sid, environ):
        client = 'ip: ' + str(environ['asgi.scope']['client'][0]) + ', sid: ' + sid + ''
        print(self.name + ' connected    \t- ' + client)

    def on_disconnect(self, sid):
        client = 'sid: ' + sid
        print(self.name + ' disconnected \t- ' + client)


class BackendServer:
    def __init__(self):
        self.host = TcpServerConfig.HOST
        self.port = TcpServerConfig.PORT
        self.r_conn, self.w_conn = Pipe(duplex=False)
        self.tcp_server = TCPServer(self.r_conn, self.w_conn)

        self.sio = None
        self.loop = None

    def run(self):
        app = FastAPI()
        self.sio = socketio.AsyncServer(async_mode=TcpServerConfig.ASYNC_MODE,
                                        cors_allowed_origins=TcpServerConfig.CORS_ORIGINS)
        tcp_server_process = self.tcp_server.get_subprocess()

        try:
            tcp_server_process.start()
            self.loop = asyncio.get_event_loop()

            socket_app = socketio.ASGIApp(self.sio, app)
            socket_server = self.web_server_load(socket_app, self.loop)

            self.loop.create_task(self.tcp_rcv_event())
            self.loop.run_until_complete(socket_server.serve())
        except Exception as e:
            print(e)
            tcp_server_process.join()
        except KeyboardInterrupt:
            tcp_server_process.join()

    def web_server_load(self, _app, loop) -> Server:
        config = Config(app=_app,
                        loop=loop,
                        host=self.host,
                        port=int(self.port))

        return Server(config)

    async def tcp_rcv_event(self):
        self.loop = asyncio.get_event_loop()
        while True:
            tcp_msg: bytes = await self.loop.run_in_executor(None, self.r_conn.recv)
            if tcp_msg is None:
                break

            tcp_event, machine_name, machine_msg = recv_protocol(tcp_msg)

            if tcp_event == TcpEventConfig.CONNECT:
                print(f'{machine_name} connected')
                dynamic_namespace_handler = CustomNamespace(namespace=machine_name)
                self.sio.register_namespace(namespace_handler=dynamic_namespace_handler)
            elif tcp_event == TcpEventConfig.DISCONNECT:
                del self.sio.namespace_handlers[machine_name]
                print(f'{machine_name} disconnected')
            elif tcp_event == TcpEventConfig.MESSAGE:
                event, data = machine_msg
                print(f'namespace : {machine_name}, event : {event}, data : {data}')
                await self.sio.emit(namespace=machine_name, event=event, data=data)
