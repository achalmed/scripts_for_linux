"""
lib/logger.py — Centralized logging for hardlinks-creator.

Provides a single logger instance with optional file output and
ANSI color support. All modules import from here so formatting
stays consistent across the entire application.
"""

import logging
import sys
from pathlib import Path


# ANSI color codes are defined here (not in a separate Colors class)
# so the logger can disable them uniformly when --no-color is set.
_COLORS = {
    "RESET":   "\033[0m",
    "BOLD":    "\033[1m",
    "GRAY":    "\033[90m",
    "RED":     "\033[91m",
    "GREEN":   "\033[92m",
    "YELLOW":  "\033[93m",
    "BLUE":    "\033[94m",
    "CYAN":    "\033[96m",
}

# Public color constants used by UI modules (ui.py imports from here)
RESET   = _COLORS["RESET"]
BOLD    = _COLORS["BOLD"]
GRAY    = _COLORS["GRAY"]
RED     = _COLORS["RED"]
GREEN   = _COLORS["GREEN"]
YELLOW  = _COLORS["YELLOW"]
BLUE    = _COLORS["BLUE"]
CYAN    = _COLORS["CYAN"]


def disable_colors() -> None:
    """
    Replaces all color constants with empty strings.
    Called once at startup when --no-color flag is detected.
    Modules that imported color constants before this call
    are NOT affected — they must import at call time or use
    the module-level attribute lookup pattern.
    """
    import lib.logger as _self
    for key in _COLORS:
        setattr(_self, key, "")


class _ColorFormatter(logging.Formatter):
    """Applies ANSI color to log level labels for console output."""

    _LEVEL_COLORS = {
        logging.DEBUG:   _COLORS["GRAY"],
        logging.INFO:    _COLORS["CYAN"],
        logging.WARNING: _COLORS["YELLOW"],
        logging.ERROR:   _COLORS["RED"],
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self._LEVEL_COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{_COLORS['RESET']}"
        return super().format(record)


def get_logger(name: str = "hardlinks-creator", verbose: bool = False,
               log_file: str | None = None) -> logging.Logger:
    """
    Builds and returns the application logger.

    Logging level is DEBUG when verbose=True, INFO otherwise.
    A file handler is added only when log_file is provided,
    without ANSI codes so the file stays clean for grep/awk.

    Args:
        name:     Logger name (shown in records).
        verbose:  When True, emit DEBUG-level messages.
        log_file: Optional path for plain-text log file.

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        # Console handler — colored
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(_ColorFormatter(
            fmt="[%(levelname)s] %(message)s"
        ))
        logger.addHandler(console)

        # File handler — plain text, appended across runs
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter(
                fmt="[%(levelname)s] %(asctime)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            logger.addHandler(fh)

    return logger
