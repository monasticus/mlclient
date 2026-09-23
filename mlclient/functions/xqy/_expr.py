"""Immutable XQuery expressions with externally bound runtime values."""

from __future__ import annotations

import datetime
import decimal
import math
import re
from collections.abc import Mapping
from abc import ABC, abstractmethod
from dataclasses import dataclass

from mlclient._experimental import experimental

# XML 1.0 NCName character ranges, excluding the QName separator ':'.
_NAME_START = (
    r"A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF"
    r"\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F"
    r"\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD"
    r"\U00010000-\U000EFFFF"
)
_NCNAME = re.compile(
    f"[{_NAME_START}][{_NAME_START}" + r".0-9\-\u00B7\u0300-\u036F\u203F-\u2040]*",
)


class _CompileContext:
    """Allocate external variables for one compilation."""

    def __init__(self):
        self._variables: dict[str, str | bool] = {}
        self._paths: list[tuple[str, str, str | None]] = []

    @property
    def variables(self) -> dict[str, str | bool]:
        """Return a copy of scalar bindings without exposing compiler state."""
        return self._variables.copy()

    def bind(self, value) -> str:
        """Bind a JSON-compatible value and return its variable reference."""
        name = f"v{len(self._variables)}"
        self._variables[name] = value
        return f"${name}"

    def path(self, source: str, kind: str, namespaces: str | None = None) -> str:
        """Register a path binding for validation before executing the whole tree."""
        ref = self.bind(source)
        self._paths.append((ref, kind, namespaces))
        return f"\0{ref}\0" if kind == "search" else ref

    def guard(self, body: str) -> str:
        """Validate every registered path before compiling the execution branch."""
        if not self._paths:
            return body
        checks = []
        for ref, kind, local_map in self._paths:
            if kind == "index" and local_map is None:
                check = f"cts:valid-index-path({ref}, fn:false())"
            else:
                arguments = ref if local_map is None else f"{ref}, {local_map}"
                check = f"cts:valid-extract-path({arguments})"
                if kind == "index":
                    check = f"cts:valid-index-path({ref}, fn:true()) and {check}"
            checks.append(
                f"if (try {{ {check} }} catch ($e) {{ fn:false() }}) then () "
                f'else <path kind="{kind}" binding="{ref[1:]}">{{{ref}}}</path>',
            )
        parts = re.split(r"\0(\$v[0-9]+)\0", body)
        fragments = [
            part if position % 2 else self.bind(part)
            for position, part in enumerate(parts)
        ]
        source = (
            fragments[0] if len(fragments) == 1
            else "fn:concat(" + ", ".join(fragments) + ")"
        )
        invalid = ", ".join(checks)
        return (
            f"let $_mlclient_invalid := ({invalid})\n"
            "return if (fn:exists($_mlclient_invalid)) then\n"
            'fn:error(fn:QName("", "MLCLIENT-INVALID-PATH"), '
            'fn:concat("Invalid XPath(s): ", fn:string-join('
            'for $p in $_mlclient_invalid return fn:concat('
            '"[", fn:string($p/@kind), ":", fn:string($p/@binding), "] ", '
            'fn:string($p)), "; ")), $_mlclient_invalid)\n'
            f"else xdmp:value({source})"
        )


def namespace_bindings(namespaces) -> dict[str, str]:
    """Copy namespace bindings and protect namespaces used by generated code.

    Parameters
    ----------
    namespaces : Mapping[str, str] | None
        User prefix-to-URI bindings; None means no additional bindings.

    Returns
    -------
    dict[str, str]
        An independent snapshot for namespace declarations or native maps.

    Raises
    ------
    TypeError
        For a non-mapping or non-string keys/values.
    ValueError
        For invalid prefixes, empty URIs or reserved compiler namespaces.
    """
    if namespaces is None:
        return {}
    if not isinstance(namespaces, Mapping):
        message = "namespaces must be a mapping of prefixes to URI strings"
        raise TypeError(message)
    result = dict(namespaces)
    for prefix, uri in result.items():
        if not isinstance(prefix, str) or not isinstance(uri, str):
            message = "namespace prefixes and URIs must be strings"
            raise TypeError(message)
        if (not uri and prefix) or prefix in {"fn", "xs", "cts", "xdmp", "map"}:
            message = f"empty or reserved namespace binding: {prefix!r}"
            raise ValueError(message)
        if prefix and _NCNAME.fullmatch(prefix) is None:
            message = f"namespace prefix must be an XML NCName: {prefix!r}"
            raise ValueError(message)
        if prefix.lower().startswith("xml"):
            message = f"reserved namespace prefix: {prefix!r}"
            raise ValueError(message)
    return result


def _namespace_declarations(namespaces: dict[str, str]) -> str:
    """Serialize declarations, escaping URI literals without changing their content."""
    declarations = []
    for prefix, uri in namespaces.items():
        literal = uri.replace("&", "&amp;").replace('"', '""')
        literal = literal.replace("\r", "&#13;").replace("\n", "&#10;")
        name = f"namespace {prefix}" if prefix else "default element namespace"
        separator = " = " if prefix else " "
        declarations.append(f'declare {name}{separator}"{literal}";\n')
    return "".join(declarations)


def _namespace_code(namespaces, ctx: _CompileContext) -> str:
    """Render a namespace map with data bindings, never interpolated URIs."""
    entries = [
        f"map:entry({ctx.bind(prefix)}, {ctx.bind(uri)})"
        for prefix, uri in namespaces.items()
    ]
    return "map:new((" + ", ".join(entries) + "))"


@experimental()
class Expr(ABC):
    """An XQuery expression, reusable in builders or ``eval.expression``."""

    @abstractmethod
    def render(self, ctx: _CompileContext) -> str:
        """Render this node, binding values through the compilation context."""

    def compile(self, *, namespaces=None) -> tuple[str, dict]:
        """Return guarded XQuery source and external bindings.

        Parameters
        ----------
        namespaces : Mapping[str, str] | None
            Prefix-to-URI bindings shared by path validation and execution.

        Returns
        -------
        tuple[str, dict]
            XQuery 1.0-ml source and independent JSON-compatible bindings.
            Invalid paths raise MLCLIENT-INVALID-PATH when evaluated.
        """
        ctx = _CompileContext()
        bindings = namespace_bindings(namespaces)
        body = ctx.guard(self.render(ctx))
        variables = ctx.variables
        prolog = 'xquery version "1.0-ml";\n'
        prolog += _namespace_declarations(bindings)
        prolog += "".join(
            f"declare variable ${name} external;\n" for name in variables
        )
        return prolog + body, variables

    def range(self, start: int, end: int) -> Expr:
        """Select inclusive, one-based positions ``start`` through ``end``.

        Parameters
        ----------
        start : int
            First position, at least one. Booleans are not positions.
        end : int
            Last position, at least ``start``.

        Returns
        -------
        Expr
            A composable positional predicate, evaluated by MarkLogic.
        """
        return _Range(self, start, end)

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
class _Range(Expr):
    """A lazy, inclusive positional predicate."""

    inner: Expr
    start: int
    end: int

    def __post_init__(self):
        if type(self.start) is not int or type(self.end) is not int:
            message = "range bounds must be integers, not booleans"
            raise TypeError(message)
        if self.start < 1 or self.end < self.start:
            message = "range bounds must satisfy 1 <= start <= end"
            raise ValueError(message)

    def render(self, ctx: _CompileContext) -> str:
        """Render the inner expression with a positional predicate."""
        return f"({self.inner.render(ctx)})[{self.start} to {self.end}]"


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


@dataclass(frozen=True)
class _Path(Expr):
    """A path string validated natively before any expression is executed."""

    source: str
    kind: str = "search"
    namespaces: Expr | None = None

    def render(self, ctx: _CompileContext) -> str:
        """Register validation and return an inline placeholder or a string binding."""
        bindings = None if self.namespaces is None else self.namespaces.render(ctx)
        return ctx.path(self.source, self.kind, bindings)


@dataclass(frozen=True)
class _NamespaceMap(Expr):
    """Immutable namespace bindings for native path-reference arguments."""

    bindings: tuple[tuple[str, str], ...]

    def render(self, ctx: _CompileContext) -> str:
        """Build a native map without exposing data as executable source."""
        return _namespace_code(dict(self.bindings), ctx)


def namespace_map(value):
    """Convert Python namespace mappings while preserving native map expressions."""
    if isinstance(value, Mapping):
        return _NamespaceMap(tuple(namespace_bindings(value).items()))
    return value


def index_path(value, namespaces=None) -> Expr:
    """Register literal index paths, including every member of a path sequence."""
    if isinstance(value, str):
        return _Path(value, "index", namespaces)
    if isinstance(value, (list, tuple)):
        return _Sequence(tuple(index_path(item, namespaces) for item in value))
    return as_expr(value)


def search_path(expression: str | Expr) -> Expr:
    """Wrap path strings internally; existing composed expressions stay composable."""
    if isinstance(expression, str):
        return _Path(expression)
    if isinstance(expression, _Raw):
        return _Path(expression.source[1:-1])
    if not isinstance(expression, Expr):
        message = "searchable expressions require a path string or Expr"
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
