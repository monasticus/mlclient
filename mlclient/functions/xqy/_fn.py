"""``fn:`` builders returning expression trees.

``Fn`` is a pure builder namespace: every method returns an ``Expr`` that wraps
another expression (typically a ``cts:`` call) and never touches a client.
``FnService`` inherits it and overrides the aggregating functions to evaluate.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._expr import Expr, _FunctionCall, as_expr


@experimental()
class Fn:
    """Pure ``fn:`` builders returning expression trees."""

    @staticmethod
    def count(sequence) -> Expr:
        """Build ``fn:count`` over a sequence expression."""
        return _FunctionCall("fn:count", [as_expr(sequence)])

    @staticmethod
    def exists(sequence) -> Expr:
        """Build ``fn:exists`` over a sequence expression."""
        return _FunctionCall("fn:exists", [as_expr(sequence)])

    @staticmethod
    def empty(sequence) -> Expr:
        """Build ``fn:empty`` over a sequence expression."""
        return _FunctionCall("fn:empty", [as_expr(sequence)])
