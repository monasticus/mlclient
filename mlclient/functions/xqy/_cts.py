"""``cts:`` query, lexicon and reference builders.

``Cts`` is a pure builder namespace: every method returns an ``Expr`` and never
touches a client. ``CtsService`` inherits it and overrides the executing
functions (search, uris, values, estimate) to compile and evaluate.
"""

from __future__ import annotations

from dataclasses import dataclass

from mlclient._experimental import experimental
from mlclient.functions.xqy._expr import (
    Expr,
    _CompileContext,
    _FunctionCall,
    _Raw,
    as_expr,
    search_path,
    write_sequence,
)
from mlclient.functions.xqy._xs import Xs

xs = Xs()

_RANGE_OPERATORS = frozenset({"<", "<=", ">", ">=", "=", "!="})
_DIRECTORY_DEPTHS = frozenset({"1", "infinity"})


@dataclass
class _Seq(Expr):
    """An XQuery sequence of runtime values."""

    items: list
    cast: str | None = None

    def render(self, ctx: _CompileContext) -> str:
        """Render the items as a comma-separated XQuery sequence."""
        return write_sequence(self.items, ctx, cast=self.cast)


def _keyword(text: str) -> _Raw:
    if '"' in text:
        message = f"keyword must not contain a quote: {text!r}"
        raise ValueError(message)
    return _Raw(f'"{text}"')


def _options(options) -> Expr | None:
    return _Seq(list(options), cast="xs:string") if options else None


def _weight(weight) -> Expr | None:
    return xs.double(weight) if weight is not None else None


def _qname(name) -> Expr:
    return name if isinstance(name, Expr) else xs.qname(name)


def _start(start) -> Expr:
    return as_expr(start) if start is not None else _Raw("()")


def _operator(operator: str) -> _Raw:
    if operator not in _RANGE_OPERATORS:
        message = f"unsupported range operator: {operator!r}"
        raise ValueError(message)
    return _keyword(operator)


def _depth(depth: str) -> _Raw:
    if depth not in _DIRECTORY_DEPTHS:
        message = f"directory depth must be '1' or 'infinity': {depth!r}"
        raise ValueError(message)
    return _keyword(depth)


@experimental()
class Cts:
    """Pure ``cts:`` builders returning expression trees."""

    @staticmethod
    def and_query(queries, *, ordered: bool | None = None) -> Expr:
        """Build ``cts:and-query``."""
        option = None if ordered is None else _keyword(_ordered(ordered))
        return _FunctionCall("cts:and-query", [_Seq(_as_list(queries))], [option])

    @staticmethod
    def or_query(queries) -> Expr:
        """Build ``cts:or-query``."""
        return _FunctionCall("cts:or-query", [_Seq(_as_list(queries))])

    @staticmethod
    def not_query(query: Expr) -> Expr:
        """Build ``cts:not-query``."""
        return _FunctionCall("cts:not-query", [query])

    @staticmethod
    def near_query(queries, *, distance=None, options=(), weight=None) -> Expr:
        """Build ``cts:near-query``."""
        distance_arg = xs.double(distance) if distance is not None else None
        return _FunctionCall(
            "cts:near-query",
            [_Seq(_as_list(queries))],
            [distance_arg, _options(options), _weight(weight)],
        )

    @staticmethod
    def word_query(text, *, options=(), weight=None) -> Expr:
        """Build ``cts:word-query``."""
        return _FunctionCall(
            "cts:word-query",
            [_Seq(_as_list(text))],
            [_options(options), _weight(weight)],
        )

    @staticmethod
    def directory_query(uris, depth: str = "1") -> Expr:
        """Build ``cts:directory-query``; ``depth`` is ``"1"`` or ``"infinity"``."""
        return _FunctionCall(
            "cts:directory-query", [_Seq(_as_list(uris)), _depth(depth)],
        )

    @staticmethod
    def document_query(uris) -> Expr:
        """Build ``cts:document-query``."""
        return _FunctionCall("cts:document-query", [_Seq(_as_list(uris))])

    @staticmethod
    def collection_query(uris) -> Expr:
        """Build ``cts:collection-query``."""
        return _FunctionCall("cts:collection-query", [_Seq(_as_list(uris))])

    @staticmethod
    def document_root(name) -> Expr:
        """Build ``cts:document-root-query`` (MarkLogic 11+)."""
        return _FunctionCall("cts:document-root-query", [_qname(name)], since=11)

    @staticmethod
    def element_value_query(element, text, *, options=(), weight=None) -> Expr:
        """Build ``cts:element-value-query``."""
        return _FunctionCall(
            "cts:element-value-query",
            [_qname(element), _Seq(_as_list(text))],
            [_options(options), _weight(weight)],
        )

    @staticmethod
    def element_word_query(element, text, *, options=(), weight=None) -> Expr:
        """Build ``cts:element-word-query``."""
        return _FunctionCall(
            "cts:element-word-query",
            [_qname(element), _Seq(_as_list(text))],
            [_options(options), _weight(weight)],
        )

    @staticmethod
    def element_range_query(
        element, operator, value, *, options=(), weight=None,
    ) -> Expr:
        """Build ``cts:element-range-query``."""
        return _FunctionCall(
            "cts:element-range-query",
            [_qname(element), _operator(operator), _value_seq(value)],
            [_options(options), _weight(weight)],
        )

    @staticmethod
    def path_range_query(path, operator, value, *, options=(), weight=None) -> Expr:
        """Build ``cts:path-range-query``."""
        return _FunctionCall(
            "cts:path-range-query",
            [_Seq(_as_list(path)), _operator(operator), _value_seq(value)],
            [_options(options), _weight(weight)],
        )

    @staticmethod
    def json_property_value_query(name, text, *, options=(), weight=None) -> Expr:
        """Build ``cts:json-property-value-query``."""
        return _FunctionCall(
            "cts:json-property-value-query",
            [_Seq(_as_list(name)), _Seq(_as_list(text))],
            [_options(options), _weight(weight)],
        )

    @staticmethod
    def true_query() -> Expr:
        """Build ``cts:true-query``."""
        return _FunctionCall("cts:true-query", [])

    @staticmethod
    def false_query() -> Expr:
        """Build ``cts:false-query``."""
        return _FunctionCall("cts:false-query", [])

    @staticmethod
    def element_reference(element, *, options=()) -> Expr:
        """Build ``cts:element-reference``."""
        return _FunctionCall(
            "cts:element-reference", [_qname(element)], [_options(options)],
        )

    @staticmethod
    def path_reference(path, *, options=()) -> Expr:
        """Build ``cts:path-reference``."""
        return _FunctionCall("cts:path-reference", [as_expr(path)], [_options(options)])

    @staticmethod
    def json_property_reference(name, *, options=()) -> Expr:
        """Build ``cts:json-property-reference``."""
        return _FunctionCall(
            "cts:json-property-reference", [as_expr(name)], [_options(options)],
        )

    @staticmethod
    def field_reference(name, *, options=()) -> Expr:
        """Build ``cts:field-reference``."""
        return _FunctionCall(
            "cts:field-reference", [as_expr(name)], [_options(options)],
        )

    @staticmethod
    def collection_reference(*, options=()) -> Expr:
        """Build ``cts:collection-reference``."""
        return _FunctionCall("cts:collection-reference", [], [_options(options)])

    @staticmethod
    def uri_reference() -> Expr:
        """Build ``cts:uri-reference``."""
        return _FunctionCall("cts:uri-reference", [])

    @staticmethod
    def search(
        expression: str = "/", query: Expr | None = None, *, options=(),
    ) -> Expr:
        """Build ``cts:search``; ``expression`` is any balanced XPath (default root)."""
        if query is None:
            message = "cts:search requires a query"
            raise ValueError(message)
        return _FunctionCall(
            "cts:search", [search_path(expression), query], [_options(options)],
        )

    @staticmethod
    def uris(
        query: Expr | None = None, *, start: str | None = None, options=(),
    ) -> Expr:
        """Build ``cts:uris`` over the URI lexicon."""
        return _FunctionCall("cts:uris", [_start(start)], [_options(options), query])

    @staticmethod
    def values(
        references, query: Expr | None = None, *, start=None, options=(),
    ) -> Expr:
        """Build ``cts:values`` over one or more range index references."""
        return _FunctionCall(
            "cts:values",
            [_Seq(_as_list(references))],
            [_start(start), _options(options), query],
        )

    @staticmethod
    def estimate(query: Expr) -> Expr:
        """Build ``cts:estimate``."""
        return _FunctionCall("cts:estimate", [query])


def _as_list(value) -> list:
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _value_seq(value) -> Expr:
    return _Seq(_as_list(value))


def _ordered(ordered: bool) -> str:
    return "ordered" if ordered else "unordered"
