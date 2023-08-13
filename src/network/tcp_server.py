import asyncio

from asyncio import transports
from multiprocessing import Process, connection

from config import TcpEventConfig, TcpServerConfig
from network.protocols import send_protocol, tcp_recv_protocol


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
        self.tcp_port = TcpServerConfig.TCP_PORT

        self.r_conn = r_conn
        self.w_conn = w_conn

    def tcp_server_process(self):
        print('TCP Server Start')
        global w_pipe
        w_pipe = self.w_conn

        try:
            loop = asyncio.get_event_loop()
            server = loop.run_until_complete(loop.create_server(TCPServerProtocol, self.host, self.tcp_port))
            loop.run_until_complete(server.wait_closed())
        except KeyboardInterrupt:
            self.w_conn.close()

    def get_subprocess(self):
        return Process(target=self.tcp_server_process, daemon=True)
