import io
import pickle
import asyncio
import socketio

from asyncio import AbstractEventLoop
from fastapi import FastAPI
from uvicorn import Config, Server
from socketio import AsyncNamespace
from multiprocessing import Process, Pipe, connection

from tcp_server import tcp_server_process


HOST = 'localhost'
PORT = 8080
TCP_PORT = 8082

app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi',
                           cors_allowed_origins='*',)
namespace_path = '/test'


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


namespace_handler = CustomNamespace(namespace=namespace_path)
sio.register_namespace(namespace_handler=namespace_handler)


def server_load(_app, loop: AbstractEventLoop, host, port):
    config = Config(app=_app,
                    loop=loop,
                    host=host,
                    port=port)
    return Server(config)


def recv_protocol(msg):
    with io.BytesIO() as memfile:
        memfile.write(msg)
        memfile.seek(0)
        tcp_event, machine_name, msg = pickle.load(memfile)
    return tcp_event, machine_name, msg


async def tcp_rcv_event(r_conn: connection.Connection):
    loop = asyncio.get_event_loop()
    while True:
        tcp_msg: bytes = await loop.run_in_executor(None, r_conn.recv)
        if tcp_msg is None:
            break

        tcp_event, machine_name, machine_msg = recv_protocol(tcp_msg)
        machine_name = '/' + machine_name

        if tcp_event == 'c':
            pass
        elif tcp_event == 'd':
            pass
        elif tcp_event == 'm':
            event, data = machine_msg
            await sio.emit(namespace=machine_name, event=event, data=data)


if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()

    r_conn, w_conn = Pipe(duplex=False)

    tcp_server_process = Process(target=tcp_server_process,
                                 kwargs={'host': HOST, 'port': TCP_PORT, 'w_conn': w_conn},
                                 daemon=True)

    try:
        tcp_server_process.start()

        socket_app = socketio.ASGIApp(sio, app)
        main_loop = asyncio.get_event_loop()
        socket_server = server_load(socket_app, main_loop, HOST, PORT)

        main_loop.create_task(tcp_rcv_event(r_conn=r_conn))
        main_loop.run_until_complete(socket_server.serve())
        r_conn.close()

    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        tcp_server_process.join()
