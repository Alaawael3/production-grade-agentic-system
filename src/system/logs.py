from pathlib import Path
import sys
from config.settings import settings, LogRenderer, Environment
import os
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
import structlog
from typing import Any, List


def get_log_file_path() -> Path:
    """Get the current log file path based on the environment.

    Returns:
        Path: The path to the log file
    """
    # get env
    env_name = str(settings.APP_ENV)

    # get file path
    file_path = Path(
        str(settings.LOG_DIR),
        f"{env_name}-log.jsonl"
    )

    # if the file folder doesn't exist then create the folder
    file_path.parent.mkdir(parents=True, exist_ok=True)

    return file_path


def get_structlog_processors(include_file_info: bool = True) -> List[Any]:
    """Get the structlog processors based on configuration.

    Args:
        include_file_info: Whether to include file information in the logs

    Returns:
        List[Any]: List of structlog processors
    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.contextvars.merge_contextvars,
    ]

    if include_file_info:
        processors.append(
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.MODULE,
                    structlog.processors.CallsiteParameter.PATHNAME,
                }
            )
        )

    # add environment info
    processors.append(
        lambda _, __, event_dict: {**event_dict, "environment": str(settings.APP_ENV)}
    )

    return processors


def sort_event_keys(_, __, event_dict):
    """Sort event keys based on priority and alphabetically."""
    priority_keys = [
        "timestamp",
        "Level",
        "event",
        "Logger",
        "environment",
        "pathname",
        "filename",
        "module",
        "func_name"
        "Lineno",
    ]
    ordered = {}

    for key in priority_keys:
        if key in event_dict:
            ordered[key] = event_dict.pop(key)

    for key in sorted(event_dict):
        ordered[key] = event_dict[key]

    return ordered


def setup_logging() -> None:
    """Configure structlog with different formatters based on environment.
    
    In development: pretty console output
    In staging/production: structured JSON logs
    """
    log_level = str(settings.LOG_LEVEL)

    # create consol handler
    consol_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(
            colors=settings.LOG_RENDERER == LogRenderer.CONSOLE
        )
    )

    console_handler = logging.StreamHandler(sys.stdout) # handler that print the logs in the console
    console_handler.setLevel(log_level)
    console_handler.setFormatter(consol_formatter)

    # create file handler for json

    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer()
    )

    # Write my logs to a file, and when the file gets too large, 
    # automatically create a new file instead of letting it grow forever
    file_handler = ConcurrentRotatingFileHandler(
        get_log_file_path(),
        mode='a', # means append.
        encoding='utf-8',
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(json_formatter)

    # configure logs in general
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=[console_handler, file_handler],
        force=True
    )

    shared_processors = get_structlog_processors(
        include_file_info=settings.APP_ENV in [Environment.STAGING, Environment.PRODUCTION]
    )

    structlog.configure(
        processors=[
            *shared_processors,
            sort_event_keys, # custom processor
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter # It connects structlog's processing pipeline to Python's standard logging system.
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True
    )


setup_logging()

logger = structlog.get_logger()

def main():
    print(f"welcome from `{os.path.basename(__file__).split('.')[0]}` modeul, nothing to do ^___^!")
    print(get_log_file_path())
    logger.info(
        "Logging_initialized",
        environment=str(settings.APP_ENV),
        log_level=str(settings.LOG_LEVEL),
        log_renderer=str(settings.LOG_RENDERER),
        debug=settings.DEBUG,
    )

    logger.debug(
        "test_debug",
        environment=str(settings.APP_ENV),
        log_level=str(settings.LOG_LEVEL),
        log_renderer=str(settings.LOG_RENDERER),
        debug=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
