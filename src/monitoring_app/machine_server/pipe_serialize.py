import io
import pickle
from enum import Enum, auto
from typing import Tuple


class MachineEvent(Enum):
    DataUpdate      : int = auto()
    FaultDetect     : int = auto()


class MachineThreadEvent(Enum):
    CONNECT: int = auto()
    DISCONNECT: int = auto()
    DATA_UPDATE: int = auto()


def pipe_serialize(event: MachineThreadEvent,
                   machine_name: str,
                   machine_event: MachineEvent = None,
                   data: any = None):
    try:
        with io.BytesIO() as memfile:
            pickle.dump((event, machine_name, machine_event, data), memfile)
            serialized = memfile.getvalue()
    except Exception:
        raise RuntimeError('pipe serialize error')

    return serialized


def pipe_deserialize(serialized: bytes) -> Tuple[MachineThreadEvent, str, MachineEvent, any]:
    try:
        with io.BytesIO() as memfile:
            memfile.write(serialized)
            memfile.seek(0)
            machine_thread_event, machine_name, machine_event, data = pickle.load(memfile)
    except Exception:
        raise RuntimeError('pipe deserialize error')

    return machine_thread_event, machine_name, machine_event, data
