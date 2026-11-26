"""Sentinel for options inherited from configuration."""

from __future__ import annotations

from enum import Enum


class UnsetType(Enum):
    """The type of UNSET, the sentinel marking an unset argument.

    UNSET is its only member. It differs from None, which is an explicit value:
    ``timeout=UNSET`` inherits the configured timeout while ``timeout=None``
    disables it. For ``auth`` it distinguishes "the caller did not choose a
    method" (so connection defaults apply) from an explicit ``auth="digest"``
    (which keeps digest even alongside a client certificate, yielding double
    auth). For ``protocol`` and ``port`` it distinguishes an omitted value
    (auto-resolved for Cloud or mutual TLS) from an explicit one that conflicts
    and must error.

    Annotate a parameter that forwards an omitted argument as
    ``timeout: httpx.Timeout | float | UnsetType | None = UNSET``. Being a
    single-member enum lets type checkers narrow ``if timeout is UNSET``.
    """

    UNSET = "UNSET"

    def __repr__(self) -> str:
        """Return the sentinel's name.

        Returns
        -------
        str
            ``"UNSET"``.
        """
        return "UNSET"

    def __str__(self) -> str:
        """Return the sentinel's name.

        Returns
        -------
        str
            ``"UNSET"``.
        """
        return "UNSET"


UNSET = UnsetType.UNSET
