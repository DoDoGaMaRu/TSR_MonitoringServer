import io
import pickle


def send_protocol(event, machine_name, data=None):
    with io.BytesIO() as memfile:
        pickle.dump((event, machine_name, data), memfile)
        serialized = memfile.getvalue()
    return serialized


def recv_protocol(msg):
    with io.BytesIO() as memfile:
        memfile.write(msg)
        memfile.seek(0)
        tcp_event, machine_name, msg = pickle.load(memfile)
    return tcp_event, machine_name, msg


def tcp_recv_protocol(msg: bytes):
    with io.BytesIO() as memfile:
        memfile.write(msg)
        memfile.seek(0)
        event, data = pickle.load(memfile)
    return event, data