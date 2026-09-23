"""XML Schema type constructors as expression builders (``xs:`` namespace).

Python scalars use typed external variables. These constructors explicitly
convert scalar values or composed expressions to the requested XQuery type.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._expr import Expr, as_expr


@experimental()
class Xs:
    """Build native XML Schema atomic type constructors.

    Each constructor accepts zero or one atomic value after atomization. Empty
    input returns an empty sequence; invalid lexical forms and unsupported
    conversions raise an error when MarkLogic evaluates the expression.

    Notes
    -----
    Constructor contract: https://www.w3.org/TR/xpath-functions/#constructor-functions
    """

    @staticmethod
    def qname(lexical: str | Expr) -> Expr:
        """Construct an xs:QName using the expression's namespace declarations.

        Parameters
        ----------
        lexical : str | Expr
            Lexical QName, optionally prefixed. The prefix must be declared
            through the expression's namespaces argument.

        Returns
        -------
        Expr
            Native xs:QName constructor. Use fn.qname for an explicit URI.

        Notes
        -----
        Constructor contract: https://www.w3.org/TR/xpath-functions/#constructor-functions
        """
        return as_expr(lexical, cast="xs:QName")

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

        Notes
        -----
        Native signature: xs:integer($arg as xs:anyAtomicType?) as xs:integer?
        Constructor contract: https://www.w3.org/TR/xpath-functions/#constructor-functions
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

        Notes
        -----
        Native signature: xs:double($arg as xs:anyAtomicType?) as xs:double?
        Constructor contract: https://www.w3.org/TR/xpath-functions/#constructor-functions
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

        Notes
        -----
        Native signature: xs:decimal($arg as xs:anyAtomicType?) as xs:decimal?
        Constructor contract: https://www.w3.org/TR/xpath-functions/#constructor-functions
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

        Notes
        -----
        Native signature: xs:dateTime($arg as xs:anyAtomicType?) as xs:dateTime?
        Constructor contract: https://www.w3.org/TR/xpath-functions/#constructor-functions
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

        Notes
        -----
        Native signature: xs:date($arg as xs:anyAtomicType?) as xs:date?
        Constructor contract: https://www.w3.org/TR/xpath-functions/#constructor-functions
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

        Notes
        -----
        Native signature: xs:string($arg as xs:anyAtomicType?) as xs:string?
        Constructor contract: https://www.w3.org/TR/xpath-functions/#constructor-functions
        """
        return as_expr(value, cast="xs:string")
