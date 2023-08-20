from socketio import AsyncNamespace


class CustomNamespace(AsyncNamespace):
    def __init__(self, namespace):
        super().__init__(namespace=namespace)
        self.name = namespace[1:]

    def on_connect(self, sid, environ):
        client = 'ip: ' + str(environ['asgi.scope']['client'][0]) + ', sid: ' + sid + ''
        print(self.name + ' connected    \t- ' + client)

    def on_disconnect(self, sid):
        client = 'sid: ' + sid
        print(self.name + ' disconnected \t- ' + client)