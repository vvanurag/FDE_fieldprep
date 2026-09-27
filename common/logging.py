"""Rich-powered logging utility for agent workflows."""

import logging
from rich.console import Console
from rich.logging import RichHandler

console = Console()


def get_logger(name: str = "agentic_ai", level: str = "INFO") -> logging.Logger:
    """Returns a structured logger configured with Rich output."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
        )
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.propagate = False
    return logger
