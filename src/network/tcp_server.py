import asyncio
import socketio

from asyncio import transports
from fastapi import FastAPI
from uvicorn import Config, Server
from socketio import AsyncNamespace
from multiprocessing import Process, connection

from config import TcpEventConfig, TcpServerConfig
from network.protocols import send_protocol, tcp_recv_protocol, recv_protocol


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


class TCPServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.machine_name = None
        self.transport = None
        self.reader = None
        self.writer = None
        self.peer_name = None

    def connection_made(self, transport: transports.WriteTransport) -> None:
        self.transport = transport
        self.reader = asyncio.StreamReader(loop=asyncio.get_event_loop())
        self.writer = asyncio.StreamWriter(transport=transport,
                                           protocol=self,
                                           reader=self.reader,
                                           loop=asyncio.get_event_loop())

        self.peer_name = transport.get_extra_info('peer_name')

        async def set_machine_name():
            self.machine_name = '/' + (await self.reader.readuntil())[:-1].decode()
            w_pipe.send(send_protocol(event=TcpEventConfig.CONNECT, machine_name=self.machine_name))
        asyncio.create_task(set_machine_name())

    def data_received(self, data):
        self.reader.feed_data(data)
        asyncio.create_task(self.handle_messages())

    async def handle_messages(self):
        while True:
            try:
                machine_event, data = tcp_recv_protocol(await self.reader.readuntil())
                # Process the received message here

                w_pipe.send(send_protocol(event=TcpEventConfig.MESSAGE,
                                          machine_name=self.machine_name,
                                          data=(machine_event, data)))
            except asyncio.IncompleteReadError:
                break
            except RuntimeError:
                break

    def connection_lost(self, exc) -> None:
        w_pipe.send(send_protocol(event=TcpEventConfig.DISCONNECT, machine_name=self.machine_name))
        self.writer.close()
        print(f'connection lost {self.machine_name}')


class TCPServer:
    def __init__(self, r_conn: connection.Connection, w_conn: connection.Connection):
        self.host = TcpServerConfig.HOST
        self.port = TcpServerConfig.PORT
        self.tcp_port = TcpServerConfig.TCP_PORT

        self.r_conn = r_conn
        self.w_conn = w_conn

        self.sio = None

    def tcp_server_process(self):
        global w_pipe
        w_pipe = self.w_conn

        try:
            loop = asyncio.get_event_loop()
            server = loop.run_until_complete(loop.create_server(TCPServerProtocol, self.host, self.tcp_port))
            loop.run_until_complete(server.wait_closed())
        except KeyboardInterrupt:
            self.w_conn.close()

    def run(self):
        tcp_server_process = Process(target=self.tcp_server_process, daemon=True)

        app = FastAPI()
        self.sio = socketio.AsyncServer(async_mode=TcpServerConfig.ASYNC_MODE,
                                        cors_allowed_origins=TcpServerConfig.CORS_ORIGINS, )

        try:
            tcp_server_process.start()

            socket_app = socketio.ASGIApp(self.sio, app)
            main_loop = asyncio.get_event_loop()
            socket_server = self.tcp_server_load(socket_app, main_loop)

            main_loop.create_task(self.tcp_rcv_event())
            main_loop.run_until_complete(socket_server.serve())
            self.r_conn.close()

        except Exception as e:
            print(e)
        except KeyboardInterrupt:
            tcp_server_process.join()

    def tcp_server_load(self, _app, loop) -> Server:
        config = Config(app=_app,
                        loop=loop,
                        host=self.host,
                        port=int(self.port))

        return Server(config)

    async def tcp_rcv_event(self):
        loop = asyncio.get_event_loop()
        while True:
            tcp_msg: bytes = await loop.run_in_executor(None, self.r_conn.recv)
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
