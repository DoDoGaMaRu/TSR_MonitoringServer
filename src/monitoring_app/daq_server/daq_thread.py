import asyncio

from asyncio import transports
from multiprocessing import connection

from config import ServerConfig
from .data_controller import DataController
from .protocols import tcp_recv_protocol, send_protocol, DAQEvent, ProtocolException


class DAQThread(asyncio.Protocol):
    def __init__(self, w_conn: connection.Connection):
        self.w_conn = w_conn

        self.dc = None
        self.machine_name = None
        self.peer_name = None
        self.transport = None
        self.writer = None
        self.reader = None

    def connection_made(self, transport: transports.WriteTransport) -> None:
        self.transport = transport
        self.reader = asyncio.StreamReader(loop=asyncio.get_event_loop())
        self.writer = asyncio.StreamWriter(transport=transport,
                                           protocol=self,
                                           reader=self.reader,
                                           loop=asyncio.get_event_loop())

        self.peer_name = transport.get_extra_info('peer_name')
        asyncio.create_task(self.set_machine_name())

    async def set_machine_name(self):
        self.machine_name = (await self.reader.readuntil(ServerConfig.SEP))[:-ServerConfig.SEP_LEN].decode()
        self.w_conn.send(send_protocol(event=DAQEvent.CONNECT, machine_name=self.machine_name))
        self.dc = DataController(self.machine_name)

    async def handle_messages(self):
        while True:
            try:
                machine_event, data = tcp_recv_protocol(await self.reader.readuntil(ServerConfig.SEP))

                await self.dc.add_data(machine_event, data)
                self.w_conn.send(send_protocol(event=DAQEvent.MESSAGE,
                                               machine_name=self.machine_name,
                                               machine_msg=(machine_event, data)))
            except ProtocolException:
                pass
            except asyncio.IncompleteReadError:
                break
            except RuntimeError:
                break

    def data_received(self, data):
        self.reader.feed_data(data)
        asyncio.create_task(self.handle_messages())

    def connection_lost(self, exc) -> None:
        self.w_conn.send(send_protocol(event=DAQEvent.DISCONNECT, machine_name=self.machine_name))
        self.writer.close()
        print(f'connection lost {self.machine_name}')
