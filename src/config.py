import configparser

config_file = 'resources/config.ini'
cfg = configparser.ConfigParser()
cfg.read(config_file)


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
