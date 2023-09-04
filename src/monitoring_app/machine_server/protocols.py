import io
import pickle
import asyncio

from enum import Enum, auto
from typing import Tuple


SEP: bytes = b'\o'
SEP_LEN: int = len(SEP)


class ProtocolException(Exception):
    pass


class MachineEvent(Enum):
    CONNECT: int = auto()
    DISCONNECT: int = auto()
    MESSAGE: int = auto()


def send_protocol(event: MachineEvent, machine_name: str, machine_msg: Tuple[str, object] = None):
    try:
        with io.BytesIO() as memfile:
            pickle.dump((event, machine_name, machine_msg), memfile)
            serialized = memfile.getvalue()
    except Exception:
        raise ProtocolException()
    return serialized


def recv_protocol(msg: bytes):
    try:
        with io.BytesIO() as memfile:
            memfile.write(msg)
            memfile.seek(0)
            tcp_event, machine_name, machine_msg = pickle.load(memfile)
    except Exception:
        raise ProtocolException()
    return tcp_event, machine_name, machine_msg


async def tcp_recv_protocol(reader: asyncio.StreamReader):
    serialized = (await reader.readuntil(SEP))[:-SEP_LEN]
    try:
        with io.BytesIO() as memfile:
            memfile.write(serialized)
            memfile.seek(0)
            event, data = pickle.load(memfile)
    except Exception:
        raise ProtocolException()
    return event, data
