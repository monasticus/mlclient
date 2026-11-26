"""Mark experimental classes for documentation and optional runtime diagnostics."""

from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

_ClassT = TypeVar("_ClassT", bound=type)

EXPERIMENTAL_NOTICE = (
    "This API is experimental and outside the stable API contract. "
    "It may change incompatibly in minor releases. "
)


def experimental(*, log_on_init: bool = False) -> Callable[[_ClassT], _ClassT]:
    """Mark a class without replacing its identity or constructor signature.

    Parameters
    ----------
    log_on_init : bool, default False
        Emit a warning when constructing an instance. Enable for job entry
        points, not their report models, to avoid per-document warning noise.

    Returns
    -------
    Callable
        A decorator attaching the notice used by API reference generation.
    """

    def decorate(cls: _ClassT) -> _ClassT:
        """Attach the notice and optionally wrap this class's constructor."""
        metadata = {
            "__experimental__": EXPERIMENTAL_NOTICE,
            "__doc__": (cls.__doc__ or "").rstrip() + "\n\n" + EXPERIMENTAL_NOTICE,
        }
        for name, value in metadata.items():
            setattr(cls, name, value)
        if log_on_init:
            init_name = "__init__"
            init = getattr(cls, init_name)

            @wraps(init)
            def initialize(self: object, *args: object, **kwargs: object) -> None:
                """Warn about experimental use and invoke the original constructor."""
                logging.getLogger(cls.__module__).warning(
                    "%s is experimental; %s",
                    cls.__name__,
                    EXPERIMENTAL_NOTICE,
                )
                init(self, *args, **kwargs)

            setattr(cls, init_name, initialize)
        return cls

    return decorate
