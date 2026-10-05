"""``xdmp:`` builders returning expression trees.

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from mlclient.functions.xqy.expressions import (
    XqyExpression,
    FunctionCall,
    as_searchable_expression,
)


class Xdmp:
    """Pure ``xdmp:`` builders returning expression trees."""

    @staticmethod
    def exists(searchable: str | XqyExpression) -> FunctionCall:
        """Return true if any fragment is selected; false if none are selected.

        Parameters
        ----------
        searchable : str | XqyExpression
            The expression to check. This must be a partially searchable XPath
            expression or a cts:search expression. Path strings are wrapped
            internally and validated by MarkLogic before evaluation.

        Returns
        -------
        FunctionCall
            Immutable expression; no request is sent until it is evaluated.

        Notes
        -----
        Native reference: https://docs.marklogic.com/xdmp:exists
        """
        return FunctionCall("xdmp:exists", (as_searchable_expression(searchable),))
