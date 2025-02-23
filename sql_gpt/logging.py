import logging
import os
import sys
import time
from functools import wraps


class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored logs"""

    COLORS = {
        "DEBUG": "\033[96m",  # Cyan
        "INFO": "\033[0m",  # Default
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[0m",  # System default (can be bold red in some terminals)
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)


# Setup logger
logger = logging.getLogger("InteractivePrompt")
logger.setLevel(getattr(logging, os.environ.get("LOG_LEVEL", "INFO")))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter("%(message)s"))
logger.addHandler(console_handler)


def log(func):
    """
    Decorator to log the start and finish of a function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            stime = time.time()
            result = func(*args, **kwargs)
            # state = args[0] if args else None
            # if state:
            #     logger.debug(f"State after {func.__name__}: {state}")
            logger.debug(f"Agent '{func.__name__}' ran for {time.time() - stime:.2f} seconds.")
        except Exception as e:
            logger.exception(f"Error in agent '{func.__name__}': {e}")
            raise
        return result

    return wrapper
