"""XML Schema type constructors as expression builders (``xs:`` namespace).

Each wraps a runtime value so it reaches MarkLogic with an explicit type rather
than the default ``xs:untypedAtomic`` an undeclared external variable carries.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._expr import Atom, Expr, _CompileContext


@experimental()
class Xs:
    """Pure ``xs:`` type constructors returning expression trees."""

    @staticmethod
    def qname(local: str, uri: str | None = None) -> Expr:
        """Build a qualified name; with ``uri`` uses ``fn:QName`` for both parts."""
        return _QName(local, uri)

    @staticmethod
    def integer(value) -> Expr:
        """Build an ``xs:integer`` value."""
        return Atom(value, cast="xs:integer")

    @staticmethod
    def double(value) -> Expr:
        """Build an ``xs:double`` value."""
        return Atom(value, cast="xs:double")

    @staticmethod
    def decimal(value) -> Expr:
        """Build an ``xs:decimal`` value."""
        return Atom(value, cast="xs:decimal")

    @staticmethod
    def date_time(value) -> Expr:
        """Build an ``xs:dateTime`` value."""
        return Atom(value, cast="xs:dateTime")

    @staticmethod
    def date(value) -> Expr:
        """Build an ``xs:date`` value."""
        return Atom(value, cast="xs:date")

    @staticmethod
    def string(value) -> Expr:
        """Build an ``xs:string`` value."""
        return Atom(value, cast="xs:string")


class _QName(Expr):
    """A QName built from runtime local name and optional namespace URI."""

    def __init__(self, local: str, uri: str | None):
        self.local = local
        self.uri = uri

    def render(self, ctx: _CompileContext) -> str:
        """Render ``xs:QName`` or, with a URI, ``fn:QName``."""
        if self.uri is not None:
            return f"fn:QName({ctx.bind(self.uri)}, {ctx.bind(self.local)})"
        return f"xs:QName({ctx.bind(self.local)})"
