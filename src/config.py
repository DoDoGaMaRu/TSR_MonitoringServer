import yaml

from typing import List

config_file = 'resources/config.yml'

with open(config_file, 'r', encoding='UTF-8') as yml:
    cfg = yaml.safe_load(yml)


class ServerConfig:
    HOST            : str = cfg['SERVER']['HOST']
    PORT            : int = cfg['SERVER']['PORT']
    TCP_PORT        : int = cfg['SERVER']['TCP_PORT']
    CORS_ORIGINS    : List[str] = cfg['SERVER']['CORS_ORIGINS']
    SIO_PREFIX      : str = '/sio'


class FCMConfig:
    CRED_PATH       : str = cfg['FCM']['CRED_PATH']
    TIMEOUT         : int = cfg['FCM']['TIMEOUT']


class LoggerConfig:
    PATH            : str = cfg['LOGGER']['PATH']
    FORMAT          : str = '%(asctime)s | %(name)s | %(levelname)s : %(message)s'


class DBConfig:
    PATH            : str = cfg['DATABASE']['PATH']
    HOUR_SUFFIX     : str = '_hour_avg'
    DAY_SUFFIX      : str = '_day_avg'


class StatConfig:
    MODE            : dict = cfg['STAT']

    _STAT_MODE = {'ABS': lambda data: list(map(abs, data)),
                  'REAL': lambda data: data}
    for sensor_type, mode in MODE.items():
        MODE[sensor_type] = _STAT_MODE[mode]

class DataConfig:
    PATH            : str = cfg['DATA']['PATH']
