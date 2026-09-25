"""``xdmp:`` builders returning expression trees.

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy.expressions import XqyExpression, _FunctionCall, search_path


@experimental()
class Xdmp:
    """Pure ``xdmp:`` builders returning expression trees."""

    @staticmethod
    def exists(searchable) -> XqyExpression:
        """Return true if any fragment is selected; false if none are selected.

        Parameters
        ----------
        searchable : object
            The expression to check. This must be a partially searchable XPath
            expression or a cts:search expression. Path strings are wrapped
            internally and validated by MarkLogic before evaluation.

        Returns
        -------
        XqyExpression
            Immutable expression; no request is sent until it is evaluated.

        Notes
        -----
        Native reference: https://docs.marklogic.com/xdmp:exists
        """
        return _FunctionCall("xdmp:exists", (search_path(searchable),))
