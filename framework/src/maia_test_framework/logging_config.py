import inspect
import logging
import sys
from typing import Optional

import structlog
from structlog.types import EventDict, Processor

from maia_test_framework.config import config


def configure_logging(json_format: bool = False) -> None:
    """Configure structured logging for the application.

    Args:
        json_format: Whether to output logs in JSON format
    """
    # Set up logging levels
    app_level = getattr(logging, config.APP_LOG_LEVEL.upper(), logging.INFO)
    deps_level = getattr(logging, config.DEPS_LOG_LEVEL.upper(), logging.WARNING)

    # Clear any existing handlers from the root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create a single handler for all loggers
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)  # Allow all logs to pass through the handler

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=deps_level,
        handlers=[handler],
    )

    # Set up specific logger levels
    logging.getLogger("src").setLevel(app_level)

    # Apply specific logger overrides from config
    for logger_name, level_str in config.LOGGER_OVERRIDES.items():
        level = getattr(logging, level_str.upper(), None)
        if level is not None:
            logging.getLogger(logger_name).setLevel(level)

    # Custom processor to add line numbers
    def add_line_number_processor(
        logger: str, method_name: str, event_dict: EventDict
    ) -> EventDict:
        # Get the caller's frame info
        frame = inspect.currentframe()
        # Go back a few frames to get the actual caller (skipping structlog internals)
        for _ in range(7):  # Skip several frames to get to the actual caller
            if frame is None:
                break
            frame = frame.f_back

        if frame:
            event_dict["line"] = frame.f_lineno
            # If there's already a logger_name, append line number to it
            if "logger_name" in event_dict:
                event_dict["logger_name"] = f"{event_dict['logger_name']}:{frame.f_lineno}"

        return event_dict

    # Configure processors for structlog
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_line_number_processor,  # Add our custom processor
    ]

    if json_format:
        # JSON formatter for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console formatter for development
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True, exception_formatter=structlog.dev.plain_traceback
            )
        )

    # Configure structlog to use the standard library logging
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with the given name.

    Args:
        name: Name for the logger, defaults to the module name

    Returns:
        A configured structured logger
    """
    return structlog.get_logger(name)
