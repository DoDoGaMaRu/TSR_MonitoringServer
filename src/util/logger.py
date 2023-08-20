import logging
import os

from config import LoggerConfig

format_ = LoggerConfig.FORMAT


def get_logger(name: str = 'log',
               log_level: any = logging.INFO,
               save_path: str = None):
    logger = logging.getLogger(name)
    set_logger(logger=logger,
               name=name,
               log_level=log_level,
               save_path=save_path)
    return logger


def set_logger(logger: logging.Logger,
               name: str = 'log',
               log_level: any = logging.INFO,
               save_path: str = None):
    logger.setLevel(log_level)

    formatter = logging.Formatter(format_)

    stream_handler = get_stream_handler(formatter)
    logger.addHandler(stream_handler)

    if save_path is not None:
        file_handler = get_file_handler(save_path, name, formatter)
        logger.addHandler(file_handler)

    return logger


def get_file_handler(path: str, name: str, formatter):
    _init_path(path)

    file_path = path + '/' + name
    handler = logging.handlers.TimedRotatingFileHandler(filename=file_path, when='midnight',
                                                        interval=1, encoding='utf-8')
    handler.suffix = "%Y%m%d.log"
    handler.setFormatter(formatter)

    return handler


def get_stream_handler(formatter):
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    return handler


def _init_path(path: str):
    if not os.path.exists(path):
        os.makedirs(path)
