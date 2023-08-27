from socketio import AsyncNamespace


class CustomNamespace(AsyncNamespace):
    def __init__(self, namespace, logger):
        super().__init__(namespace=namespace)
        self.name = namespace[1:]
        self.logger = logger

    def on_connect(self, sid, environ):
        self.logger.info(f"{self.name} connected - ip: {environ['asgi.scope']['client'][0]}, sid: {sid}")

    def on_disconnect(self, sid):
        self.logger.info(f"{self.name} disconnected - sid: {sid}")
