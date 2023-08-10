import io
import pickle
import datetime
import socket
import time
from threading import Thread

HOST = 'localhost'
PORT = 8082
THIS_NAME = 'client1'


def run():
    global inspectionCount, sock, partsNum, lastINS, modelChange

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect((HOST, PORT))
        sock.settimeout(None)

        while True:
            data = sock.recv(1024)
            if not data:
                break
            msg = data.decode('ascii')
            print(datetime.datetime.now(), msg)
        sock.close()


def send_protocol(event, data):
    with io.BytesIO() as memfile:
        pickle.dump([event, data], memfile)
        serialized = memfile.getvalue()
    return serialized + b'\n'


while True:
    try:
        t = Thread(target=run, daemon=True)
        t.start()

        machine_name = input('machine name : ')
        sock.sendall((machine_name + '\n').encode())
        while True:
            event = input('event : ')
            msg = input('send : ')

            sock.sendall(send_protocol(event, msg))

    except Exception as e:
        time.sleep(1)
        print(e)
