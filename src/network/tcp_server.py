import asyncio
import socketio

from asyncio import transports, AbstractEventLoop
from fastapi import FastAPI
from uvicorn import Config, Server
from socketio import AsyncNamespace
from multiprocessing import Process, Pipe, connection

from config import TcpEventConfig, TcpServerConfig
from protocols import send_protocol, tcp_recv_protocol, recv_protocol


class TCPServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.machine_name = None
        self.transport = None
        self.reader = None
        self.writer = None
        self.peername = None

    def connection_made(self, transport: transports.WriteTransport) -> None:
        self.transport = transport
        self.reader = asyncio.StreamReader(loop=asyncio.get_event_loop())
        self.writer = asyncio.StreamWriter(transport=transport,
                                           protocol=self,
                                           reader=self.reader,
                                           loop=asyncio.get_event_loop())

        self.peername = transport.get_extra_info('peername')

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


class BackendServer:
    def __init__(self):
        self.host = TcpServerConfig.HOST
        self.port = TcpServerConfig.PORT
        self.tcp_port = TcpServerConfig.TCP_PORT

        self.r_conn, self.w_conn = Pipe(duplex=False)
        self.tcp_server_process = Process(target=self.tcp_server_process,
                                          kwargs={'host': TcpServerConfig.HOST, 'port': TcpServerConfig.TCP_PORT},
                                          daemon=True)

    def tcp_server_process(self):
        global w_pipe
        w_pipe = self.w_conn

        try:
            loop = asyncio.get_event_loop()
            server = loop.run_until_complete(loop.create_server(TCPServerProtocol, self.host, self.port))
            loop.run_until_complete(server.wait_closed())
        except KeyboardInterrupt:
            self.w_conn.close()
