from network.tcp_server import TCPServer
from multiprocessing import Pipe


class BackendServer:
    def __init__(self):
        self.r_conn, self.w_conn = Pipe(duplex=False)

        self.tcp_server = TCPServer(self.r_conn, self.w_conn)
        self.web_server = None #TODO 구현 필요

    def run(self):
        self.tcp_server.run()
        #self.web_server.run()
