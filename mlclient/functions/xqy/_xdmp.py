"""``xdmp:`` builders returning expression trees.

``Xdmp`` is a pure builder namespace: every method returns an ``Expr`` and never
touches a client. ``XdmpService`` inherits it and overrides the executing
functions to evaluate.
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

        ``searchable`` is an ``Expr`` (e.g. a ``cts:search`` call) or a bare
        absolute XPath string. Unlike ``fn:exists`` it resolves from indexes
        without materialising nodes, so it is the preferred database-wide
        existence check.
        """
        argument = (
            search_path(searchable) if isinstance(searchable, str) else searchable
        )
        return _FunctionCall("xdmp:exists", [argument])
