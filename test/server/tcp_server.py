from __future__ import annotations

import io
import pickle
import asyncio
from asyncio import transports
from multiprocessing.connection import Connection


def send_protocol(event, machine_name, data=None):
    with io.BytesIO() as memfile:
        pickle.dump([event, machine_name, data], memfile)
        serialized = memfile.getvalue()
    return serialized


def tcp_recv_protocol(msg: bytes):
    with io.BytesIO() as memfile:
        memfile.write(msg)
        memfile.seek(0)
        event, data = pickle.load(memfile)
    return event, data


class TCPServerProtocol(asyncio.Protocol):
    def connection_made(self, transport: transports.WriteTransport) -> None:
        self.peername = 'test' # TODO transport.get_extra_info('peername')
        print(f'Connection from {self.peername}')
        self.transport = transport
        self.reader = asyncio.StreamReader(loop=asyncio.get_event_loop())
        self.writer = asyncio.StreamWriter(transport=transport,
                                           protocol=self,
                                           reader=self.reader,
                                           loop=asyncio.get_event_loop())
        w_pipe.send(send_protocol(event='c', machine_name=self.peername))

        # TODO transport에 extrainfo 속성이 있는것으로 보아 클라이언트의 속성을 받을 수 있는것으로 보임, 해당부분 확인 필요

    def data_received(self, data):
        self.reader.feed_data(data)
        asyncio.create_task(self.handle_messages())

    async def handle_messages(self):
        while True:
            try:
                # TODO 지금은 encode() 된 문자열만 가능함
                machine_event, data = tcp_recv_protocol(await self.reader.readuntil())
                # Process the received message here

                w_pipe.send(send_protocol(event='m',
                                          machine_name=self.peername,
                                          data=(machine_event, data)))
            except asyncio.IncompleteReadError:
                break
            except RuntimeError:
                break

    def connection_lost(self, exc: Exception | None) -> None:
        print('connection lost')
        self.writer.close()


def tcp_server_process(host: str, port: int, w_conn: Connection):
    global w_pipe
    w_pipe = w_conn

    try:
        loop = asyncio.get_event_loop()
        server = loop.run_until_complete(loop.create_server(TCPServerProtocol, host, port))
        loop.run_until_complete(server.wait_closed())
    except KeyboardInterrupt:
        w_pipe.close()
