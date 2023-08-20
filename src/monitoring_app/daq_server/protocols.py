import io
import pickle
from enum import Enum, auto
from typing import Tuple


class ProtocolException(Exception):
    pass


class DAQEvent(Enum):
    CONNECT: str = auto()
    DISCONNECT: str = auto()
    MESSAGE: str = auto()


def send_protocol(event, machine_name, machine_msg: Tuple[str, object] = None):
    try:
        with io.BytesIO() as memfile:
            pickle.dump((event, machine_name, machine_msg), memfile)
            serialized = memfile.getvalue()
    except Exception:
        raise ProtocolException()
    return serialized


def recv_protocol(msg):
    try:
        with io.BytesIO() as memfile:
            memfile.write(msg)
            memfile.seek(0)
            tcp_event, machine_name, machine_msg = pickle.load(memfile)
    except Exception:
        raise ProtocolException()
    return tcp_event, machine_name, machine_msg


def tcp_recv_protocol(msg: bytes):
    try:
        with io.BytesIO() as memfile:
            memfile.write(msg)
            memfile.seek(0)
            event, data = pickle.load(memfile)
    except Exception:
        raise ProtocolException()
    return event, data
