"""The ``--timeout`` option of the commands that send a request to MarkLogic.

A client-side timeout only stops waiting for the answer: MarkLogic keeps
running the request, so an update may still commit after the command failed.
"""

from __future__ import annotations

import math

import httpx
from cleo.helpers import option
from cleo.io.inputs.option import Option

from mlclient._options import UNSET, _Unset
from mlclient.exceptions import WrongParametersError

_EXPIRED_COMPONENTS = {
    httpx.ConnectTimeout: "connect",
    httpx.ReadTimeout: "read",
    httpx.WriteTimeout: "write",
    httpx.PoolTimeout: "pool",
}


def timeout_option() -> Option:
    """Define the ``--timeout SECONDS`` option.

    Returns
    -------
    Option
        A value option read with :func:`parse_timeout`.
    """
    return option(
        "timeout",
        description="Seconds to wait for MarkLogic, 0 waits indefinitely "
        "(default: connect 5, read 60); a timed-out request may still run on "
        "the server and an update may still commit",
        flag=False,
    )


def parse_timeout(
    value: str | None,
) -> float | None | _Unset:
    """Turn the ``--timeout`` value into a per-request timeout argument.

    Parameters
    ----------
    value : str | None
        The option value, or None when the option is absent.

    Returns
    -------
    float | None | _Unset
        Seconds for all four HTTP timeout components; None for ``0``, which
        disables the HTTP timeout; UNSET when absent, keeping the client's
        default timeout.

    Raises
    ------
    WrongParametersError
        If the value is not a finite, non-negative number.
    """
    if value is None:
        return UNSET
    try:
        seconds = float(value)
    except ValueError:
        seconds = math.nan
    if not math.isfinite(seconds) or seconds < 0:
        msg = f"--timeout must be a non-negative number of seconds, got: {value!r}"
        raise WrongParametersError(msg)
    return seconds or None


def timed_out_message(
    error: httpx.TimeoutException,
) -> str:
    """Describe an expired HTTP timeout in one line.

    Parameters
    ----------
    error : httpx.TimeoutException
        The timeout raised by httpx; its request carries the timeout applied.

    Returns
    -------
    str
        The configured duration when available, and a warning that the request
        may still be running on the server. Custom transports may omit the
        request or its timeout metadata.
    """
    component = next(
        (
            name
            for error_type, name in _EXPIRED_COMPONENTS.items()
            if isinstance(error, error_type)
        ),
        None,
    )
    try:
        seconds = error.request.extensions.get("timeout", {}).get(component)
    except RuntimeError:
        seconds = None
    duration = f" after {seconds:g}s" if seconds is not None else ""
    return f"Request timed out{duration} - it may still be running on the server"
