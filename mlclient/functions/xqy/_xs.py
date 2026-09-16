"""XML Schema type constructors as expression builders (``xs:`` namespace).

Each wraps a runtime value so it reaches MarkLogic with an explicit type rather
than the default ``xs:untypedAtomic`` an undeclared external variable carries.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._expr import Expr, _FunctionCall, as_expr


@experimental()
class Xs:
    """Pure ``xs:`` type constructors returning expression trees."""

    @staticmethod
    def qname(local: str | Expr, uri: str | Expr | None = None) -> Expr:
        """Build a qualified name; with ``uri`` uses ``fn:QName`` for both parts.

        Parameters
        ----------
        local : str | Expr
            Lexical QName, optionally including a prefix.
        uri : str | Expr | None
            Namespace URI; when supplied, construct the name with fn:QName.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return (
            _FunctionCall("fn:QName", (uri, local))
            if uri is not None
            else as_expr(local, cast="xs:QName")
        )

    @staticmethod
    def integer(value) -> Expr:
        """Build an ``xs:integer`` value.

        Parameters
        ----------
        value : object
            Scalar or expression yielding zero or one atomic value. Multiple
            items are rejected by the native type constructor.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return as_expr(value, cast="xs:integer")

    @staticmethod
    def double(value) -> Expr:
        """Build an ``xs:double`` value.

        Parameters
        ----------
        value : object
            Scalar or expression yielding zero or one atomic value. Multiple
            items are rejected by the native type constructor.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return as_expr(value, cast="xs:double")

    @staticmethod
    def decimal(value) -> Expr:
        """Build an ``xs:decimal`` value.

        Parameters
        ----------
        value : object
            Scalar or expression yielding zero or one atomic value. Multiple
            items are rejected by the native type constructor.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return as_expr(value, cast="xs:decimal")

    @staticmethod
    def date_time(value) -> Expr:
        """Build an ``xs:dateTime`` value.

        Parameters
        ----------
        value : object
            Scalar or expression yielding zero or one atomic value. Multiple
            items are rejected by the native type constructor.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return as_expr(value, cast="xs:dateTime")

    @staticmethod
    def date(value) -> Expr:
        """Build an ``xs:date`` value.

        Parameters
        ----------
        value : object
            Scalar or expression yielding zero or one atomic value. Multiple
            items are rejected by the native type constructor.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return as_expr(value, cast="xs:date")

    @staticmethod
    def string(value) -> Expr:
        """Build an ``xs:string`` value.

        Parameters
        ----------
        value : object
            Scalar or expression yielding zero or one atomic value. Multiple
            items are rejected by the native type constructor.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return as_expr(value, cast="xs:string")
