"""Register MLClient's diagnostic logging level using the standard library."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast


def _logger_fine(
    logger: logging.Logger,
    message: object,
    *args: object,
    **kwargs: Any,  # noqa: ANN401 - forwarded to Logger.log as its keyword options
) -> None:
    """Log at FINE, forwarding logging options and identifying the caller."""
    kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
    logger.log(
        logging.FINE,  # type: ignore[attr-defined]
        message,
        *args,
        **kwargs,
    )


def _root_fine(
    message: object,
    *args: object,
    **kwargs: Any,  # noqa: ANN401 - forwarded to Logger.log as its keyword options
) -> None:
    """Log at FINE through the root logger, preserving logging options."""
    kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig()
    root.log(
        logging.FINE,  # type: ignore[attr-defined]
        message,
        *args,
        **kwargs,
    )


if TYPE_CHECKING:

    class _FineLogger(logging.Logger):
        """A standard logger with MLClient's registered FINE method."""

        fine = _logger_fine


def get_logger(name: str) -> _FineLogger:
    """Get a standard logger with its registered FINE method typed.

    Parameters
    ----------
    name : str
        Logger name, normally the calling module's name.

    Returns
    -------
    logging.Logger
        The standard logging registry's logger, including the FINE extension.
        No new logger class or handler is installed.
    """
    return cast("_FineLogger", logging.getLogger(name))


def register_fine_logging() -> None:
    """Make FINE available as a level and as logger/module convenience methods.

    Existing registrations are retained so importing MLClient does not replace
    an application's logging extensions. Repeated registration is harmless.
    FINE defaults to one level below DEBUG. No handlers are configured here.
    """
    if not hasattr(logging, "FINE"):
        vars(logging)["FINE"] = logging.DEBUG - 1
        logging.addLevelName(
            logging.FINE,  # type: ignore[attr-defined]
            "FINE",
        )
    for target, name, method in (
        (logging.Logger, "fine", _logger_fine),
        (logging, "fine", _root_fine),
    ):
        if not hasattr(target, name):
            setattr(target, name, method)
