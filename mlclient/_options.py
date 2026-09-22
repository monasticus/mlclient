"""Sentinel for options inherited from configuration."""

from __future__ import annotations


class _Unset:
    """Sentinel marking an unset argument.

    For ``auth`` it distinguishes "the caller did not choose a method" (so
    connection defaults apply) from an explicit ``auth="digest"`` (which keeps
    digest even alongside a client certificate, yielding double auth). For
    ``protocol`` and ``port`` it distinguishes an omitted value (auto-resolved
    for Cloud or mutual TLS) from an explicit one that conflicts and must error.
    """

    def __repr__(self) -> str:
        return "UNSET"


UNSET = _Unset()
