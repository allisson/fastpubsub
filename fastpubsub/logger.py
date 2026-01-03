"""Logging utilities for fastpubsub application."""

import logging

from pythonjsonlogger.json import JsonFormatter

from fastpubsub.config import settings


def get_log_level(level: str) -> int:
    """Convert string log level to logging module constant.

    Args:
        level: Log level as a string (debug, info, warning, error, critical).

    Returns:
        Integer constant for the log level from the logging module.

    Raises:
        AttributeError: If the level string is not valid.
    """
    return getattr(logging, level.upper())


def get_console_handler() -> logging.StreamHandler:
    """Create and configure a console handler with JSON formatter.

    Returns:
        Configured StreamHandler with JSON formatter for console output.
    """
    formatter = JsonFormatter(settings.log_formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    return console_handler


def get_logger(name: str) -> logging.Logger:
    """Create and configure a logger with the specified name.

    Args:
        name: Name for the logger, typically __name__ from the calling module.

    Returns:
        Configured logger instance with appropriate log level and handlers.
    """
    logger = logging.getLogger(name)
    log_level = get_log_level(settings.log_level)
    logger.setLevel(log_level)
    logger.addHandler(get_console_handler())
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger
