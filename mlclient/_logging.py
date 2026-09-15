"""Register MLClient's diagnostic logging level using the standard library."""

from __future__ import annotations

import logging
from typing import Any


def _logger_fine(logger: logging.Logger, message: object, *args: Any, **kwargs: Any):
    """Log at FINE, forwarding logging options and identifying the caller."""
    kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
    logger.log(logging.FINE, message, *args, **kwargs)


def _root_fine(message: object, *args: Any, **kwargs: Any):
    """Log at FINE through the root logger, preserving logging options."""
    kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig()
    root.log(logging.FINE, message, *args, **kwargs)


def register_fine_logging() -> None:
    """Make FINE available as a level and as logger/module convenience methods.

    Existing registrations are retained so importing MLClient does not replace
    an application's logging extensions. Repeated registration is harmless.
    FINE defaults to one level below DEBUG. No handlers are configured here.
    """
    if not hasattr(logging, "FINE"):
        logging.FINE = logging.DEBUG - 1
        logging.addLevelName(logging.FINE, "FINE")
    if not hasattr(logging.Logger, "fine"):
        logging.Logger.fine = _logger_fine
    if not hasattr(logging, "fine"):
        logging.fine = _root_fine
