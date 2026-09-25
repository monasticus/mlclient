"""XQuery expressions, compilation context and namespace validation.

Public types are specific to XQuery; no shared SJS compilation contract is implied.
"""

from __future__ import annotations

import datetime
import decimal
import math
import re
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
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


class XqyCompilationContext:
    """Bindings and path validation for one XQuery expression compilation.

    Custom XqyExpression.render implementations use this context to bind runtime
    values. XqyExpression.compile creates a fresh context for every invocation.
    """

    def __init__(self):
        """Create an empty context for one compilation."""
        self._variables: dict[str, str | bool] = {}
        self._paths: list[tuple[str, str]] = []
        self._types: dict[str, str] = {}

    @property
    def variables(self) -> dict[str, str | bool]:
        """Return a copy of scalar bindings without exposing compiler state."""
        return self._variables.copy()

    def bind(self, value, atomic_type: str = "xs:string") -> str:
        """Bind a JSON-compatible value and return its variable reference."""
        name = f"v{len(self._variables)}"
        self._variables[name] = value
        self._types[name] = atomic_type
        return f"${name}"

    @property
    def declarations(self) -> str:
        """Return typed declarations without exposing mutable compiler state."""
        return "".join(
            f"declare variable ${name} as {atomic_type} external;\n"
            for name, atomic_type in self._types.items()
        )

    def path(self, source: str, kind: str) -> str:
        """Bind a code path and register its role for validation diagnostics."""
        ref = self.bind(source)
        self._paths.append((ref, kind))
        return f"\0{ref}\0"

    def guard(self, body: str) -> str:
        """Validate code paths before compiling the complete execution source."""
        if not self._paths:
            return body
        paths = ",\n    ".join(
            f'<path kind="{kind}" binding="{ref[1:]}">{{{ref}}}</path>'
            for ref, kind in self._paths
        )
        body = re.sub(
            r"\x00\$(v[0-9]+)\x00",
            lambda match: self._variables[match[1]],
            body,
        )
        source = self.bind(body)
        return (
            f"let $invalid-paths := (\n    {paths}\n)[fn:not(\n"
            "    try { cts:valid-extract-path(.) }\n"
            "    catch ($error) { fn:false() }\n"
            ")]\n"
            "return if (fn:empty($invalid-paths)) then\n"
            f"    xdmp:value({source})\n"
            "else\n"
            '    fn:error(fn:QName("", "MLCLIENT-INVALID-PATH"),\n'
            '        fn:concat("Invalid XPath(s): ", fn:string-join(\n'
            "            for $path in $invalid-paths\n"
            '            return fn:concat("[", fn:string($path/@kind), ":",\n'
            '                fn:string($path/@binding), "] ", fn:string($path)),\n'
            '            "; ")),\n'
            "        $invalid-paths)"
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


def _namespace_code(namespaces, ctx: XqyCompilationContext) -> str:
    """Render a namespace map with data bindings, never interpolated URIs."""
    entries = [
        f"map:entry({ctx.bind(prefix)}, {ctx.bind(uri)})"
        for prefix, uri in namespaces.items()
    ]
    if len(entries) == 1:
        return entries[0]
    return "map:new((" + ", ".join(entries) + "))"


@experimental()
class XqyExpression(ABC):
    """An XQuery expression, reusable in builders or ``eval.expression``."""

    @abstractmethod
    def render(self, ctx: XqyCompilationContext) -> str:
        """Render this expression using the shared compilation context.

        Parameters
        ----------
        ctx : XqyCompilationContext
            Context for binding runtime values and registering path validation.

        Returns
        -------
        str
            XQuery body fragment. Runtime data must be bound, not interpolated.
        """

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
        ctx = XqyCompilationContext()
        bindings = namespace_bindings(namespaces)
        body = ctx.guard(self.render(ctx))
        variables = ctx.variables
        prolog = 'xquery version "1.0-ml";\n'
        prolog += _namespace_declarations(bindings)
        prolog += ctx.declarations
        return prolog + body, variables

    def range(
        self,
        start: int | XqyExpression,
        end: int | XqyExpression,
    ) -> XqyExpression:
        """Select inclusive, one-based positions ``start`` through ``end``.

        Parameters
        ----------
        start : int | XqyExpression
            Positive integer or fn.last(). Booleans are not positions.
        end : int | XqyExpression
            Positive integer or fn.last(); literal bounds must be ordered.

        Returns
        -------
        XqyExpression
            A composable positional predicate, evaluated by MarkLogic.
        """
        return _Range(self, start, end)

    def index(self, position: int | XqyExpression) -> XqyExpression:
        """Select one item by its one-based position.

        Parameters
        ----------
        position : int | XqyExpression
            Positive integer or fn.last(), evaluated inside the predicate.

        Returns
        -------
        XqyExpression
            Selected item, or an empty sequence if the position does not exist.
        """
        _validate_position(position)
        return _Index(self, position)

    def xpath(self, path: str) -> XqyExpression:
        """Extract a restricted XPath from each result item in sequence order.

        Parameters
        ----------
        path : str
            Non-empty native extraction path. Relative paths start at each item;
            absolute paths start at its root. Uses compilation namespaces.

        Returns
        -------
        XqyExpression
            A simple-map expression. Apply index/range before this method to
            select hits before applying this XPath.

        Raises
        ------
        TypeError
            If path is not a string.
        ValueError
            If path is empty or whitespace-only. Native syntax validation occurs
            during evaluation, before executing the composed expression.
        """
        return _ResultXPath(self, path)

    def __str__(self) -> str:
        """Return compiled XQuery source without the external bindings."""
        return self.compile()[0]


@dataclass(frozen=True)
class _AtomicValue(XqyExpression):
    """An immutable scalar represented by a JSON-safe lexical value."""

    value: str | bool
    cast: str | None = None

    def render(self, ctx: XqyCompilationContext) -> str:
        """Bind the scalar and restore its XQuery type."""
        return ctx.bind(self.value, self.cast or "xs:string")


class _DatabaseRoot(XqyExpression):
    """The fixed document-node path used by default searches."""

    def render(self, _ctx: XqyCompilationContext) -> str:
        """Return the built-in database root; no user source is involved."""
        return "/"


def _validate_position(value: int | XqyExpression) -> None:
    """Require a positive integer or the native zero-argument fn:last call."""
    if type(value) is int:
        if value < 1:
            message = "index/range positions must be positive"
            raise ValueError(message)
    elif not (
        isinstance(value, _FunctionCall)
        and value.fn == "fn:last"
        and not value.args
        and not value.optionals
    ):
        message = "index/range positions must be integers or fn.last()"
        raise TypeError(message)


@dataclass(frozen=True)
class _Index(XqyExpression):
    """A single positional predicate."""

    inner: XqyExpression
    position: int | XqyExpression

    def render(self, ctx: XqyCompilationContext) -> str:
        """Keep fn:last inside the selected sequence's predicate context."""
        position = as_expr(self.position).render(ctx)
        inner = self.inner.render(ctx)
        if not isinstance(
            self.inner,
            (_FunctionCall, ModuleFunctionCall, _Index, _Range),
        ):
            inner = f"({inner})"
        return f"{inner}[{position}]"


@dataclass(frozen=True)
class _Range(XqyExpression):
    """A lazy, inclusive positional predicate."""

    inner: XqyExpression
    start: int | XqyExpression
    end: int | XqyExpression

    def __post_init__(self):
        _validate_position(self.start)
        _validate_position(self.end)
        if type(self.start) is int and type(self.end) is int and self.end < self.start:
            message = "range bounds must satisfy 1 <= start <= end"
            raise ValueError(message)

    def render(self, ctx: XqyCompilationContext) -> str:
        """Render bounds inside the predicate to preserve their context."""
        inner = self.inner.render(ctx)
        if not isinstance(
            self.inner,
            (_FunctionCall, ModuleFunctionCall, _Index, _Range),
        ):
            inner = f"({inner})"
        start = as_expr(self.start).render(ctx)
        end = as_expr(self.end).render(ctx)
        return f"{inner}[{start} to {end}]"


@dataclass(frozen=True)
class _ResultXPath(XqyExpression):
    """Apply a validated extraction path to each selected search hit in order."""

    inner: XqyExpression
    source: str

    def __post_init__(self):
        """Validate result XPath input before sending a request.

        Raises
        ------
        TypeError
            If source is not a string.
        ValueError
            If source is empty or whitespace-only.
        """
        if not isinstance(self.source, str):
            message = "xpath must be a string"
            raise TypeError(message)
        if not self.source.strip():
            message = "xpath must not be empty"
            raise ValueError(message)

    def render(self, ctx: XqyCompilationContext) -> str:
        """Map the guarded path over hits without imposing document order.

        Parameters
        ----------
        ctx : XqyCompilationContext
            Shared bindings and native path validation for this evaluation.

        Returns
        -------
        str
            Simple-map expression preserving the inner sequence's hit order.
        """
        inner = self.inner.render(ctx)
        if not isinstance(self.inner, (_FunctionCall, _Index, _Range)):
            inner = f"({inner})"
        return f"{inner} ! {ctx.path(self.source, 'xpath')}"


@dataclass(frozen=True)
class _Sequence(XqyExpression):
    """A snapshot of an XQuery sequence's child expressions."""

    items: tuple[XqyExpression, ...]

    def render(self, ctx: XqyCompilationContext) -> str:
        """Render a sequence, including the empty sequence."""
        return "(" + ", ".join(item.render(ctx) for item in self.items) + ")"


@dataclass(frozen=True)
class _FunctionCall(XqyExpression):
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

    def render(self, ctx: XqyCompilationContext) -> str:
        """Trim omitted trailing slots; retain empty interior slots."""
        optionals = list(self.optionals)
        while optionals and optionals[-1] is None:
            optionals.pop()
        parts = [arg.render(ctx) for arg in self.args]
        parts += [arg.render(ctx) if arg is not None else "()" for arg in optionals]
        return f"{self.fn}({', '.join(parts)})"


@experimental()
class ModuleFunctionCall(XqyExpression):
    """A composable call to a function in a deployed XQuery library module.

    The module is resolved with xdmp:function and invoked with xdmp:apply.
    No namespace declarations or module imports are added to the query prolog.
    """

    def __init__(
        self,
        name: str,
        args: Sequence[object] = (),
        optionals: Sequence[object] = (),
        *,
        namespace: str,
        module_path: str,
    ):
        """Capture a module function and its arguments without performing I/O.

        Parameters
        ----------
        name : str
            Function local name (an XML NCName), without a namespace prefix.
        args : Sequence[object], default ()
            Positional arguments, including Python values or XqyExpression
            instances. A nested list/tuple is one sequence-valued argument;
            None is an explicit empty-sequence argument.
        optionals : Sequence[object], default ()
            Optional trailing slots. Trailing None slots are omitted; interior
            None slots become empty sequences. Use args to pass a trailing
            empty sequence explicitly. Both argument collections are snapshotted.
        namespace : str
            Non-empty module namespace URI. It need not be an HTTP URL.
        module_path : str
            Non-empty module location resolved by the App Server. The module
            must already be deployed and accessible to the evaluating user.

        Raises
        ------
        TypeError
            If name, namespace or module_path is not a string, or an argument
            cannot be represented as an XQuery expression.
        ValueError
            If an identifier is blank or the function name is not an NCName.

        Notes
        -----
        Names, paths and argument values are bound as data, never interpolated
        into XQuery source. Application code should choose the module and function;
        binding them does not authorize executing an arbitrary library.
        Missing modules/functions and arity/type errors are reported by MarkLogic
        during evaluation, not during compilation.
        """
        for field, value in (
            ("name", name),
            ("namespace", namespace),
            ("module_path", module_path),
        ):
            if not isinstance(value, str):
                message = f"{field} must be a string"
                raise TypeError(message)
            if not value.strip():
                message = f"{field} must not be blank"
                raise ValueError(message)
        if _NCNAME.fullmatch(name) is None:
            message = "function name must be an XML NCName without a prefix"
            raise ValueError(message)
        function = _FunctionCall(
            "xdmp:function",
            (_FunctionCall("fn:QName", (namespace, name)), module_path),
        )
        self._call = _FunctionCall("xdmp:apply", (function, *args), optionals)

    def render(self, ctx: XqyCompilationContext) -> str:
        """Render native module invocation in the shared compilation context.

        Parameters
        ----------
        ctx : XqyCompilationContext
            Context shared with nested calls for typed bindings and path guards.

        Returns
        -------
        str
            An xdmp:apply expression using an explicitly namespaced function.
        """
        return self._call.render(ctx)


def xpath(source: str) -> XqyExpression:
    """Build a path validated before execution, including inside nested functions.

    Parameters
    ----------
    source : str
        Non-empty extraction XPath, not arbitrary XQuery code. EQNames such as
        ``/Q{https://monasticus.com/mlclient/examples/example}item`` avoid relying
        on namespace declarations.

    Returns
    -------
    XqyExpression
        A path expression, validated by cts:valid-extract-path before evaluation.
        Ordinary strings passed to builders remain externally bound values.

    Raises
    ------
    TypeError
        If source is not a string.
    ValueError
        If source is empty or whitespace-only.
    """
    return _Path(source)


@dataclass(frozen=True)
class _Path(XqyExpression):
    """A path string validated natively before any expression is executed."""

    source: str
    kind: str = "xpath"

    def __post_init__(self):
        """Require non-empty path text before registering server-side validation.

        Raises
        ------
        TypeError
            If source is not a string.
        ValueError
            If source is empty or whitespace-only.
        """
        if not isinstance(self.source, str):
            message = "xpath source must be a string"
            raise TypeError(message)
        if not self.source.strip():
            message = "xpath source must not be empty"
            raise ValueError(message)

    def render(self, ctx: XqyCompilationContext) -> str:
        """Register validation and return a placeholder in the execution source."""
        return ctx.path(self.source, self.kind)


@dataclass(frozen=True)
class _NamespaceMap(XqyExpression):
    """Immutable namespace bindings for native path-reference arguments."""

    bindings: tuple[tuple[str, str], ...]

    def render(self, ctx: XqyCompilationContext) -> str:
        """Build a native map without exposing data as executable source."""
        return _namespace_code(dict(self.bindings), ctx)


def namespace_map(value):
    """Convert Python namespace mappings while preserving native map expressions."""
    if isinstance(value, Mapping):
        return _NamespaceMap(tuple(namespace_bindings(value).items()))
    return value


def search_path(expression: str | XqyExpression) -> XqyExpression:
    """Wrap path strings internally; existing composed expressions stay composable."""
    if isinstance(expression, str):
        return _Path(expression, "search")
    if not isinstance(expression, XqyExpression):
        message = "searchable expressions require a path string or XqyExpression"
        raise TypeError(message)
    return expression


def as_expr(value, *, cast: str | None = None) -> XqyExpression:
    """Snapshot supported values as expressions; lists/tuples are sequences."""
    if isinstance(value, XqyExpression):
        expr = value
    elif value is None:
        expr = _Sequence(())
    elif isinstance(value, (list, tuple)):
        expr = _Sequence(tuple(as_expr(item) for item in value))
    else:
        expr = _scalar(value)
    if isinstance(expr, _AtomicValue) and expr.cast == cast:
        return expr
    if isinstance(expr, _FunctionCall) and expr.fn == cast:
        return expr
    return _FunctionCall(cast, (expr,)) if cast else expr


def _scalar(value) -> _AtomicValue:
    """Encode scalars without losing precision in the JSON transport."""
    if isinstance(value, bool):
        atom = _AtomicValue(value, "xs:boolean")
    elif isinstance(value, int):
        atom = _AtomicValue(str(value), "xs:integer")
    elif isinstance(value, float):
        lexical = (
            ("NaN" if math.isnan(value) else "INF" if value > 0 else "-INF")
            if not math.isfinite(value)
            else repr(value)
        )
        atom = _AtomicValue(lexical, "xs:double")
    elif isinstance(value, decimal.Decimal):
        if not value.is_finite():
            message = "xs:decimal requires a finite Decimal"
            raise ValueError(message)
        atom = _AtomicValue(format(value, "f"), "xs:decimal")
    elif isinstance(value, datetime.datetime):
        atom = _AtomicValue(value.isoformat(), "xs:dateTime")
    elif isinstance(value, datetime.date):
        atom = _AtomicValue(value.isoformat(), "xs:date")
    elif isinstance(value, str):
        atom = _AtomicValue(value)
    else:
        message = f"unsupported XQuery value type: {type(value).__name__}"
        raise TypeError(message)
    return atom
