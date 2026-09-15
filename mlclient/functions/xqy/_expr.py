"""Expression tree and compiler for XQuery function builders.

Every builder (cts, xs, fn) produces an ``Expr``. Compiling an ``Expr`` yields
an XQuery snippet plus a variables mapping: structure and MarkLogic keywords are
inlined, while every runtime value travels as an external variable so no
user-supplied value is ever interpolated into the source.
"""

from __future__ import annotations

import datetime
import decimal
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from mlclient._experimental import experimental


class _CompileContext:
    """Allocates ``$vN`` external variables and collects their bound values."""

    def __init__(self):
        self.variables: dict = {}
        self.requirements: list[tuple[str, int]] = []

    def bind(self, value) -> str:
        """Bind a runtime value to a fresh external variable and return its ref."""
        name = f"v{len(self.variables)}"
        self.variables[name] = value
        return f"${name}"

    def require(self, fn: str, since: int | None) -> None:
        """Record that ``fn`` needs MarkLogic major version ``since`` or later."""
        if since is not None:
            self.requirements.append((fn, since))


@experimental()
class Expr(ABC):
    """A node in an XQuery expression tree."""

    @abstractmethod
    def render(self, ctx: _CompileContext) -> str:
        """Render this node to XQuery, binding runtime values via ``ctx``."""

    def compile(self) -> tuple[str, dict]:
        """Return the runnable XQuery and its external variable bindings."""
        ctx = _CompileContext()
        body = self.render(ctx)
        prolog = "".join(
            f"declare variable ${name} external;\n" for name in ctx.variables
        )
        return prolog + body, ctx.variables

    def version_requirements(self) -> list[tuple[str, int]]:
        """Return ``(function, since-major)`` pairs for every version-gated call."""
        ctx = _CompileContext()
        self.render(ctx)
        return ctx.requirements

    def __str__(self) -> str:
        return self.compile()[0]


@dataclass
class Atom(Expr):
    """A runtime value bound as an external variable.

    ``cast`` wraps the variable in a type constructor (e.g. ``xs:string``). When
    omitted it is inferred from the Python type, so ``1`` compiles as
    ``xs:integer`` without an explicit ``xs:`` wrapper. Strings stay untyped
    (``xs:untypedAtomic``), which coerces freely in text and range contexts.
    """

    value: object
    cast: str | None = None

    def render(self, ctx: _CompileContext) -> str:
        """Bind the value and wrap it in its (given or inferred) type."""
        ref = ctx.bind(self.value)
        cast = self.cast or _infer_cast(self.value)
        return f"{cast}({ref})" if cast else ref


_INFERRED_CASTS = (
    (bool, "xs:boolean"),
    (int, "xs:integer"),
    (float, "xs:double"),
    (decimal.Decimal, "xs:decimal"),
    (datetime.datetime, "xs:dateTime"),
    (datetime.date, "xs:date"),
)


def _infer_cast(value) -> str | None:
    for python_type, cast in _INFERRED_CASTS:
        if isinstance(value, python_type):
            return cast
    return None


@dataclass
class _Raw(Expr):
    """Verbatim XQuery. Trusted, developer-supplied source - never a value."""

    source: str

    def render(self, _ctx: _CompileContext) -> str:
        """Return the trusted source unchanged; binds no runtime value."""
        return self.source


@dataclass
class _Window(Expr):
    """A ``(inner)[lo to hi]`` positional slice over ``inner``'s result sequence.

    Bounds are inlined literals, not bound variables: they are structural
    positions (validated integers, so injection-safe), and a literal range lets
    MarkLogic evaluate ``cts:search`` lazily instead of materialising every hit.
    """

    inner: Expr
    lo: int
    hi: int

    def render(self, ctx: _CompileContext) -> str:
        """Render the inner expression wrapped in a ``[lo to hi]`` predicate."""
        return f"({self.inner.render(ctx)})[{self.lo} to {self.hi}]"


@dataclass
class _FunctionCall(Expr):
    """A namespaced ``prefix:name(...)`` call. Trailing empty optionals are dropped."""

    fn: str
    args: list
    optionals: list = field(default_factory=list)
    since: int | None = None

    def render(self, ctx: _CompileContext) -> str:
        """Render the call, omitting trailing empty optional arguments."""
        ctx.require(self.fn, self.since)
        parts = [arg.render(ctx) for arg in self.args]
        optionals = list(self.optionals)
        while optionals and optionals[-1] is None:
            optionals.pop()
        parts += [o.render(ctx) if o is not None else "()" for o in optionals]
        return f"{self.fn}({', '.join(parts)})"


def search_path(path: str) -> _Raw:
    """Wrap a searchable path expression, rejecting any attempt to break out.

    The argument is a node expression, not a value, so it is inlined rather than
    bound. Any XPath is allowed as long as its parentheses stay balanced with the
    nesting depth never going negative (respecting string literals) - a stray
    ``)`` is the only way to escape the enclosing call, and a legitimate XPath
    never has one. The result is parenthesised, so top-level commas form a
    sequence rather than extra call arguments.
    """
    depth = 0
    quote = None
    index = 0
    while index < len(path):
        char = path[index]
        if quote is not None:
            if char == quote:
                if path[index + 1:index + 2] == quote:
                    index += 2
                    continue
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                break
        index += 1
    if quote is not None or depth != 0:
        message = f"unbalanced search path expression: {path!r}"
        raise ValueError(message)
    return _Raw(f"({path})")


def as_expr(value, *, cast: str | None = None) -> Expr:
    """Wrap a plain Python value as an ``Atom``, passing ``Expr`` through."""
    return value if isinstance(value, Expr) else Atom(value, cast)


def write_sequence(items, ctx: _CompileContext, *, cast: str | None = None) -> str:
    """Render a comma-separated XQuery sequence, binding each runtime value."""
    rendered = ", ".join(as_expr(item, cast=cast).render(ctx) for item in items)
    return f"({rendered})"
