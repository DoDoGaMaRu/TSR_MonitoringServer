import yaml

config_file = 'resources/config.yml'

with open(config_file, 'r', encoding='UTF-8') as yml:
    cfg = yaml.safe_load(yml)


class TcpServerConfig:
    HOST: str = cfg['TCP_SERVER']['HOST']
    PORT: int = cfg['TCP_SERVER']['PORT']
    TCP_PORT: int = cfg['TCP_SERVER']['TCP_PORT']
    ASYNC_MODE: str = cfg['TCP_SERVER']['ASYNC_MODE']
    CORS_ORIGINS: str = cfg['TCP_SERVER']['CORS_ORIGINS']


class TcpEventConfig:
    CONNECT: str = cfg['TCP_EVENT']['CONNECT']
    DISCONNECT: str = cfg['TCP_EVENT']['DISCONNECT']
    MESSAGE: str = cfg['TCP_EVENT']['MESSAGE']
