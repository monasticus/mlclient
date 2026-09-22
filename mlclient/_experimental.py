"""Mark experimental classes for documentation and optional runtime diagnostics."""

from __future__ import annotations

import logging
from functools import wraps

EXPERIMENTAL_NOTICE = (
    "This API is experimental and outside the stable API contract. "
    "It may change incompatibly in minor releases. "
)


def experimental(*, log_on_init: bool = False):
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

    def decorate(cls):
        """Attach the notice and optionally wrap this class's constructor."""
        cls.__experimental__ = EXPERIMENTAL_NOTICE
        cls.__doc__ = (cls.__doc__ or "").rstrip() + "\n\n" + EXPERIMENTAL_NOTICE
        if log_on_init:
            init = cls.__init__

            @wraps(init)
            def initialize(self, *args, **kwargs):
                """Warn about experimental use and invoke the original constructor."""
                logging.getLogger(cls.__module__).warning(
                    "%s is experimental; %s",
                    cls.__name__,
                    EXPERIMENTAL_NOTICE,
                )
                init(self, *args, **kwargs)

            cls.__init__ = initialize
        return cls

    return decorate
