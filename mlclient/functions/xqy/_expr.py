"""Immutable XQuery expressions with externally bound runtime values."""

from __future__ import annotations

import datetime
import decimal
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from mlclient._experimental import experimental


class _CompileContext:
    """Allocate external variables for one compilation."""

    def __init__(self):
        self.variables: dict = {}

    def bind(self, value) -> str:
        """Bind a JSON-compatible value and return its variable reference."""
        name = f"v{len(self.variables)}"
        self.variables[name] = value
        return f"${name}"


@experimental()
class Expr(ABC):
    """An XQuery expression, reusable in builders or ``eval.expression``."""

    @abstractmethod
    def render(self, ctx: _CompileContext) -> str:
        """Render this node, binding values through the compilation context."""

    def compile(self) -> tuple[str, dict]:
        """Return XQuery 1.0-ml source and JSON-compatible external bindings."""
        ctx = _CompileContext()
        body = self.render(ctx)
        prolog = 'xquery version "1.0-ml";\n' + "".join(
            f"declare variable ${name} external;\n" for name in ctx.variables
        )
        return prolog + body, ctx.variables

    def window(self, lo: int, hi: int) -> Expr:
        """Select inclusive, one-based positions ``lo`` through ``hi``.

        Parameters
        ----------
        lo : int
            First position, at least one. Booleans are not positions.
        hi : int
            Last position, at least ``lo``.

        Returns
        -------
        Expr
            A composable positional predicate, evaluated by MarkLogic.
        """
        return _Window(self, lo, hi)

    def __str__(self) -> str:
        return self.compile()[0]


@dataclass(frozen=True)
class Atom(Expr):
    """An immutable scalar represented by a JSON-safe lexical value."""

    value: str | bool
    cast: str | None = None

    def render(self, ctx: _CompileContext) -> str:
        """Bind the scalar and restore its XQuery type."""
        ref = ctx.bind(self.value)
        return f"{self.cast}({ref})" if self.cast else ref


@dataclass(frozen=True)
class _Raw(Expr):
    """Trusted source; never constructed implicitly from a runtime value."""

    source: str

    def render(self, _ctx: _CompileContext) -> str:
        """Return trusted source unchanged."""
        return self.source


@dataclass(frozen=True)
class _Window(Expr):
    """A lazy, inclusive positional predicate."""

    inner: Expr
    lo: int
    hi: int

    def __post_init__(self):
        if type(self.lo) is not int or type(self.hi) is not int:
            message = "window bounds must be integers, not booleans"
            raise TypeError(message)
        if self.lo < 1 or self.hi < self.lo:
            message = "window bounds must satisfy 1 <= lo <= hi"
            raise ValueError(message)

    def render(self, ctx: _CompileContext) -> str:
        """Render the inner expression with a positional predicate."""
        return f"({self.inner.render(ctx)})[{self.lo} to {self.hi}]"


@dataclass(frozen=True)
class _Sequence(Expr):
    """A snapshot of an XQuery sequence's child expressions."""

    items: tuple[Expr, ...]

    def render(self, ctx: _CompileContext) -> str:
        """Render a sequence, including the empty sequence."""
        return "(" + ", ".join(item.render(ctx) for item in self.items) + ")"


@dataclass(frozen=True)
class _FunctionCall(Expr):
    """A function call; ``None`` optional slots mean omitted arguments."""

    fn: str
    args: tuple = ()
    optionals: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, "args", tuple(as_expr(arg) for arg in self.args))
        object.__setattr__(
            self,
            "optionals",
            tuple(None if arg is None else as_expr(arg) for arg in self.optionals),
        )

    def render(self, ctx: _CompileContext) -> str:
        """Trim omitted trailing slots; retain empty interior slots."""
        optionals = list(self.optionals)
        while optionals and optionals[-1] is None:
            optionals.pop()
        parts = [arg.render(ctx) for arg in self.args]
        parts += [arg.render(ctx) if arg is not None else "()" for arg in optionals]
        return f"{self.fn}({', '.join(parts)})"


def xpath(source: str) -> Expr:
    """Embed trusted XPath/XQuery source, without parsing or sanitizing it.

    Parameters
    ----------
    source : str
        Developer-controlled source. Never pass user input here. Prefer builders
        with externally bound values for dynamic data. EQNames such as
        ``/Q{urn:example}item`` avoid relying on namespace declarations.

    Returns
    -------
    Expr
        A parenthesized source expression, suitable for ``cts.search`` and
        ``xdmp.exists`` as well as general expression composition.
    """
    if not isinstance(source, str):
        message = "xpath source must be a string"
        raise TypeError(message)
    if not source.strip():
        message = "xpath source must not be empty"
        raise ValueError(message)
    return _Raw(f"({source})")


def search_path(expression: Expr) -> Expr:
    """Require explicit source ownership at the searchable-expression boundary."""
    if not isinstance(expression, Expr):
        message = "searchable expressions require an Expr; use xpath for trusted source"
        raise TypeError(message)
    return expression


def as_expr(value, *, cast: str | None = None) -> Expr:
    """Snapshot supported values as expressions; lists/tuples are sequences."""
    if isinstance(value, Expr):
        expr = value
    elif value is None:
        expr = _Sequence(())
    elif isinstance(value, (list, tuple)):
        expr = _Sequence(tuple(as_expr(item) for item in value))
    else:
        expr = _scalar(value)
    if isinstance(expr, Atom) and expr.cast == cast:
        return expr
    return _FunctionCall(cast, (expr,)) if cast else expr


def _scalar(value) -> Atom:  # noqa: PLR0911 - one explicit conversion per supported type
    """Encode scalars without losing precision in the JSON transport."""
    if isinstance(value, bool):
        return Atom(value, "xs:boolean")
    if isinstance(value, int):
        return Atom(str(value), "xs:integer")
    if isinstance(value, float):
        lexical = (
            ("NaN" if math.isnan(value) else "INF" if value > 0 else "-INF")
            if not math.isfinite(value)
            else repr(value)
        )
        return Atom(lexical, "xs:double")
    if isinstance(value, decimal.Decimal):
        if not value.is_finite():
            message = "xs:decimal requires a finite Decimal"
            raise ValueError(message)
        return Atom(format(value, "f"), "xs:decimal")
    if isinstance(value, datetime.datetime):
        return Atom(value.isoformat(), "xs:dateTime")
    if isinstance(value, datetime.date):
        return Atom(value.isoformat(), "xs:date")
    if isinstance(value, str):
        return Atom(value)
    message = f"unsupported XQuery value type: {type(value).__name__}"
    raise TypeError(message)
