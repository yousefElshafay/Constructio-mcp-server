import logging
import sys
from typing import Any

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None  # type: ignore


def setup_logger(name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name or "api")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        if jsonlogger:
            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )
        else:
            # Fallback to standard logging if library is missing
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


logger = setup_logger()
