from typing import Dict

from socketio import AsyncNamespace

from monitoring_app.machine_server import MachineEvent


class StateSaver:
    def __init__(self, maximum_count: int):
        self._maximum_count = maximum_count
        self._datas = []

    def add_data(self, data):
        self._datas.append(data)
        if len(self._datas) > self._maximum_count:
            del self._datas[0]

    def get_datas(self):
        return self._datas


class CustomNamespace(AsyncNamespace):
    machine_event_to_str = {
        MachineEvent.DataUpdate: 'update',
        MachineEvent.FaultDetect: 'anomaly'
    }

    def __init__(self, namespace, logger):
        super().__init__(namespace=namespace)
        self.name = namespace[1:]
        self.logger = logger

        self._maximum_save = 60
        self._state_savers: Dict[str, StateSaver] = {}

    async def on_connect(self, sid, environ):
        self.logger.info(f"{self.name} connected - ip: {environ['asgi.scope']['client'][0]}, sid: {sid}")
        for state_saver in self._state_savers.values():
            await self.emit(event='initialize', data=state_saver.get_datas(), to=sid)

    async def on_disconnect(self, sid):
        self.logger.info(f"{self.name} disconnected - sid: {sid}")

    async def send_machine_event(self, machine_event: MachineEvent, data: any):
        if machine_event == MachineEvent.DataUpdate:
            if data['sensor_name'] not in self._state_savers:
                self._state_savers[data['sensor_name']] = StateSaver(self._maximum_save)
            self._state_savers[data['sensor_name']].add_data(data)
        await self.emit(event=self.machine_event_to_str[machine_event], data=data)
