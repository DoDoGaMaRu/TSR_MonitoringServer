import yaml
from typing import List

config_file = 'resources/config.yml'

with open(config_file, 'r', encoding='UTF-8') as yml:
    cfg = yaml.safe_load(yml)


class TcpServerConfig:
    HOST: str = cfg['TCP_SERVER']['HOST']
    PORT: int = cfg['TCP_SERVER']['PORT']
    TCP_PORT: int = cfg['TCP_SERVER']['TCP_PORT']
    CORS_ORIGINS: List[str] = [origin.strip() for origin in cfg['TCP_SERVER']['CORS_ORIGINS'].split(',')]


class TcpEventConfig:
    CONNECT: str = cfg['TCP_EVENT']['CONNECT']
    DISCONNECT: str = cfg['TCP_EVENT']['DISCONNECT']
    MESSAGE: str = cfg['TCP_EVENT']['MESSAGE']
