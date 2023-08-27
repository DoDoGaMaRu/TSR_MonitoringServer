from pyfcm import FCMNotification
from config import FCMConfig


class FCMSender(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        cls = type(self)
        if not hasattr(cls, "_init"):
            self._init_fcm()
            cls._init = True

    def _init_fcm(self):
        try:
            self.push_service = FCMNotification(FCMConfig.API_KEY)
        except:
            self.push_service = None

    def send(self, topic: str, title, body):
        print(title, body)
        if self.push_service is not None:
            message = {
                'title': title,
                'body': body
            }

            res = self.push_service.notify_topic_subscribers(topic_name=topic,
                                                             data_message=message)
            print(res)
