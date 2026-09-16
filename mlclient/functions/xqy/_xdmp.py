"""``xdmp:`` builders returning expression trees.

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._expr import Expr, _FunctionCall, search_path


@experimental()
class Xdmp:
    """Pure ``xdmp:`` builders returning expression trees."""

    @staticmethod
    def exists(searchable) -> Expr:
        """Build ``xdmp:exists``.

        Parameters
        ----------
        searchable : Expr
            Partially searchable path or cts:search expression; wrap trusted
            source in xpath.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("xdmp:exists", [search_path(searchable)])
