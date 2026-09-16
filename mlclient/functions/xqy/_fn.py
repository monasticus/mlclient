"""``fn:`` builders returning expression trees.

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._expr import Expr, _FunctionCall


@experimental()
class Fn:
    """Pure ``fn:`` builders returning expression trees."""

    @staticmethod
    def count(sequence, *, maximum=None) -> Expr:
        """Build ``fn:count`` over a sequence expression.

        Parameters
        ----------
        sequence : object
            Expression or supported Python values; lists/tuples become XQuery
            sequences.
        maximum : int | float | Expr | None
            Native maximum count; None leaves the count uncapped.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "fn:count",
            [sequence],
            [maximum],
        )

    @staticmethod
    def exists(sequence) -> Expr:
        """Build ``fn:exists`` over a sequence expression.

        Parameters
        ----------
        sequence : object
            Expression or supported Python values; lists/tuples become XQuery
            sequences.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("fn:exists", [sequence])

    @staticmethod
    def empty(sequence) -> Expr:
        """Build ``fn:empty`` over a sequence expression.

        Parameters
        ----------
        sequence : object
            Expression or supported Python values; lists/tuples become XQuery
            sequences.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("fn:empty", [sequence])
