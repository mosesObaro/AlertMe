"""Structured logging and error tracking."""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Create logs directory
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "app.log"


class MemoryLogHandler(logging.Handler):
    """Stores recent log records in memory for health checks and reports."""
    def __init__(self, capacity: int = 200):
        super().__init__()
        self.capacity = capacity
        self.records: List[logging.LogRecord] = []
        self.error_count = 0
        self.warning_count = 0

    def emit(self, record: logging.LogRecord):
        if record.levelno >= logging.ERROR:
            self.error_count += 1
        elif record.levelno >= logging.WARNING:
            self.warning_count += 1
        self.records.append(record)
        if len(self.records) > self.capacity:
            self.records.pop(0)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "recent_errors": [
                r.getMessage() for r in self.records if r.levelno >= logging.ERROR
            ][-10:]
        }


_memory_handler = MemoryLogHandler()


def setup_logger(name: str = "edge_phd", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File Handler
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    except Exception:
        pass

    logger.addHandler(_memory_handler)
    return logger


def get_logger_metrics() -> Dict[str, Any]:
    """Returns runtime logging metrics (errors, warnings)."""
    return _memory_handler.get_summary()


logger = setup_logger()
