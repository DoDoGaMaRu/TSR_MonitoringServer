import abc
import asyncio

from typing import Tuple
from multiprocessing import Process, Pipe

from .protocols import recv_protocol, DAQEvent
from .daq_thread import DAQThread


class EventHandler(abc.ABC):
    @abc.abstractmethod
    async def __call__(self, daq_event: DAQEvent, machine_name: str, machine_msg: Tuple[str, object]):
        pass


class Runner:
    def __init__(self,
                 host: str,
                 port: int,
                 event_handler: EventHandler):
        self.host = host
        self.port = port
        self.event_handler = event_handler
        self.r_conn, self.w_conn = Pipe(duplex=False)

        self.daq_server_process = None

    def _daq_server_process(self):
        try:
            loop = asyncio.get_event_loop()
            server = loop.run_until_complete(loop.create_server(protocol_factory=lambda: DAQThread(self.w_conn),
                                                                host=self.host,
                                                                port=self.port))
            loop.run_until_complete(server.wait_closed())
        except KeyboardInterrupt:
            self.w_conn.close()

    async def pipe_rcv_event(self):
        loop = asyncio.get_event_loop()
        while True:
            tcp_msg: bytes = await loop.run_in_executor(None, self.r_conn.recv)
            if tcp_msg is None:
                break

            daq_event, machine_name, machine_msg = recv_protocol(tcp_msg)
            await self.event_handler(daq_event, machine_name, machine_msg)

    def run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.pipe_rcv_event())

        self.daq_server_process = Process(target=self._daq_server_process, daemon=True)
        self.daq_server_process.start()

    def join(self):
        self.r_conn.close()
        self.daq_server_process.join()
