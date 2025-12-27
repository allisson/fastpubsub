import logging

from pythonjsonlogger.json import JsonFormatter

from fastpubsub.config import settings


def get_log_level(level: str) -> int:
    return getattr(logging, level.upper())


def get_console_handler() -> logging.StreamHandler:
    formatter = JsonFormatter(settings.log_formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    return console_handler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    log_level = get_log_level(settings.log_level)
    logger.setLevel(log_level)
    logger.addHandler(get_console_handler())
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger
