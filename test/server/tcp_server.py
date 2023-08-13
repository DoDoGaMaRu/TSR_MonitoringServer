import io
import pickle
import asyncio
from asyncio import transports
from multiprocessing.connection import Connection
from config import TcpEventConfig


def send_protocol(event, machine_name, data=None):
    with io.BytesIO() as memfile:
        pickle.dump((event, machine_name, data), memfile)
        serialized = memfile.getvalue()
    return serialized


def tcp_recv_protocol(msg: bytes):
    with io.BytesIO() as memfile:
        memfile.write(msg)
        memfile.seek(0)
        event, data = pickle.load(memfile)
    return event, data


class TCPServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.machine_name = None

    def connection_made(self, transport: transports.WriteTransport) -> None:
        self.transport = transport
        self.reader = asyncio.StreamReader(loop=asyncio.get_event_loop())
        self.writer = asyncio.StreamWriter(transport=transport,
                                           protocol=self,
                                           reader=self.reader,
                                           loop=asyncio.get_event_loop())

        self.peername = transport.get_extra_info('peername')

        async def set_machine_name():
            while True:
                try:
                    self.machine_name = '/' + (await self.reader.readuntil())[:-1].decode()
                    w_pipe.send(send_protocol(event=TcpEventConfig.CONNECT, machine_name=self.machine_name))
                    break
                except asyncio.IncompleteReadError:
                    break
                except RuntimeError:
                    break
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


def tcp_server_process(host: str, port: int, w_conn: Connection):
    global w_pipe
    w_pipe = w_conn

    try:
        loop = asyncio.get_event_loop()
        server = loop.run_until_complete(loop.create_server(TCPServerProtocol, host, port))
        loop.run_until_complete(server.wait_closed())
    except KeyboardInterrupt:
        w_pipe.close()
