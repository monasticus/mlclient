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
        """Return the number of items in the value of the sequence.

        Parameters
        ----------
        sequence : object
            The sequence of items to count. Lists and tuples become XQuery
            sequences.
        maximum : int | float | Expr | None
            The maximum value of the count to return. MarkLogic Server stops
            counting when this value is reached and returns it. This is an
            extension to the W3C standard fn:count function. None omits it.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:count
        """
        return _FunctionCall(
            "fn:count",
            [sequence],
            [maximum],
        )

    @staticmethod
    def exists(sequence) -> Expr:
        """Return true if the sequence is not empty; otherwise return false.

        Parameters
        ----------
        sequence : object
            A sequence to test. Lists and tuples become XQuery sequences.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:exists
        """
        return _FunctionCall("fn:exists", [sequence])

    @staticmethod
    def empty(sequence) -> Expr:
        """Return true if the sequence is empty; otherwise return false.

        Parameters
        ----------
        sequence : object
            A sequence to test. Lists and tuples become XQuery sequences.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:empty
        """
        return _FunctionCall("fn:empty", [sequence])
