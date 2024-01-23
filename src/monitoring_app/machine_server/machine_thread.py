import io
import pickle
import asyncio

from asyncio import transports, Protocol
from multiprocessing import connection

from .pipe_serialize import pipe_serialize, MachineThreadEvent
from .data_handler import DataHandler

SEP: bytes = b'\o'
SEP_LEN: int = len(SEP)


class MachineThread(Protocol):
    def __init__(self, w_conn: connection.Connection):
        self.w_conn = w_conn

        self.data_handler = None
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
        msg = await self.reader.readuntil(SEP)
        machine_event, data = self.deserialize(msg)
        self.machine_name = data
        self.w_conn.send(pipe_serialize(event=MachineThreadEvent.CONNECT, machine_name=self.machine_name))
        self.data_handler = DataHandler(self.machine_name, self.w_conn)

    async def handle_messages(self):
        while True:
            try:
                msg = await self.reader.readuntil(SEP)
                machine_event, data = self.deserialize(msg)
                await self.data_handler.data_processing(machine_event, data)
            except asyncio.IncompleteReadError:
                break
            except RuntimeError:
                break

    def data_received(self, data):
        self.reader.feed_data(data)
        asyncio.create_task(self.handle_messages())

    def connection_lost(self, exc) -> None:
        self.w_conn.send(pipe_serialize(event=MachineThreadEvent.DISCONNECT, machine_name=self.machine_name))
        self.writer.close()

    def deserialize(self, serialized: bytes):
        try:
            with io.BytesIO() as memfile:
                memfile.write(serialized[:-SEP_LEN])
                memfile.seek(0)
                event, data = pickle.load(memfile)
        except Exception:
            raise RuntimeError('deserialize error')
        return event, data
