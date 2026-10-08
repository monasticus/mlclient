"""``xdmp:`` builders returning expression trees.

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from mlclient.xquery.expressions import (
    XqyExpression,
    NodeInput,
    FunctionCall,
    StringInput,
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


    @staticmethod
    def unquote(
        arg: str | NodeInput,
        *,
        default_namespace: str | XqyExpression | None = None,
        options: StringInput = None,
    ) -> FunctionCall:
        """Build a native call parsing XML or JSON text into document nodes.

        Parameters
        ----------
        arg : str | NodeInput
            Input text to parse. Without an explicit format option, input
            starting with '{' or '[' is JSON; other input is XML. Python nodes
            supply their atomized text using the native function's type rules.
        default_namespace : str | XqyExpression | None, optional
            Default namespace for XML nodes in the input. None omits this slot
            unless options are supplied, in which case it is an empty sequence.
        options : StringInput, optional
            Native parsing options, such as repair-none, repair-full,
            format-xml, format-json, format-text, format-binary or
            default-language=en. None retains the native defaults.

        Returns
        -------
        FunctionCall
            Composable expression; building it makes no request. Evaluate it
            explicitly to parse on the server. CTS serializers can read literal
            input locally when no namespace or parsing options are supplied.

        Notes
        -----
        Native reference: https://docs.marklogic.com/xdmp:unquote
        """
        return FunctionCall("xdmp:unquote", (arg,), (default_namespace, options))
