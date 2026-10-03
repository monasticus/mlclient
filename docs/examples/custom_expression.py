"""Expose a deployed XQuery module as a family of Python expression builders."""

from __future__ import annotations

from mlclient.functions.xqy import ModuleFunctionCall, XqyExpression

_NAMESPACE = "https://monasticus.com/mlclient/examples/labels"
_MODULE_PATH = "/ext/example/labels.xqy"


class Label:
    """Build calls to the application's label module without executing them."""

    @staticmethod
    def normalize(value: str | XqyExpression) -> XqyExpression:
        """Build a call that normalizes whitespace and uppercases a label.

        Parameters
        ----------
        value : str | XqyExpression
            Label text or an expression evaluated as the function's argument.

        Returns
        -------
        XqyExpression
            A composable call; evaluate it with ml.eval.expression.
        """
        return ModuleFunctionCall(
            "normalize",
            (value,),
            namespace=_NAMESPACE,
            module_path=_MODULE_PATH,
        )

    @staticmethod
    def join(
        first: str | XqyExpression,
        second: str | XqyExpression,
        *,
        separator: str | XqyExpression | None = None,
    ) -> XqyExpression:
        """Build a call joining two labels with an optional separator.

        Parameters
        ----------
        first : str | XqyExpression
            First label or an expression producing it.
        second : str | XqyExpression
            Second label or an expression producing it.
        separator : str | XqyExpression | None
            Separator; None selects the module's two-argument overload,
            which uses a space. An empty string joins without a separator.

        Returns
        -------
        XqyExpression
            A composable call; evaluate it with ml.eval.expression.
        """
        return ModuleFunctionCall(
            "join",
            (first, second),
            optionals=(separator,),
            namespace=_NAMESPACE,
            module_path=_MODULE_PATH,
        )


label = Label()
