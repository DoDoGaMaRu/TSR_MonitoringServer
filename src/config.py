import yaml

from typing import List

config_file = 'resources/config.yml'

with open(config_file, 'r', encoding='UTF-8') as yml:
    cfg = yaml.safe_load(yml)


class ServerConfig:
    HOST            : str = cfg['TCP_SERVER']['HOST']
    PORT            : int = cfg['TCP_SERVER']['PORT']
    TCP_PORT        : int = cfg['TCP_SERVER']['TCP_PORT']
    CORS_ORIGINS    : List[str] = [origin.strip() for origin in cfg['TCP_SERVER']['CORS_ORIGINS'].split(',')]

    SIO_PREFIX      : str = '/sio'
    SEP             : bytes = b'\o'
    SEP_LEN         : int = len(SEP)


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
    for key in MODE.keys():
        MODE[key] = _STAT_MODE[MODE[key]]
