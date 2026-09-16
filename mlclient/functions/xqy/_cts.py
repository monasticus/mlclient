"""``cts:`` query, lexicon and reference builders.

``Cts`` is a pure builder namespace: every method returns an ``Expr`` and never
touches a client. ``CtsService`` executes search, uris, values and estimate.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._expr import (
    Expr,
    _FunctionCall,
    as_expr,
    search_path,
    xpath,
)
from mlclient.functions.xqy._xs import Xs

xs = Xs()

_RANGE_OPERATORS = frozenset({"<", "<=", ">", ">=", "=", "!="})
_DIRECTORY_DEPTHS = frozenset({"1", "infinity"})


def _weight(weight) -> Expr | None:
    return xs.double(weight) if weight is not None else None


def _qname(name) -> Expr:
    if isinstance(name, (list, tuple)):
        return as_expr(tuple(_qname(item) for item in name))
    return name if isinstance(name, Expr) else xs.qname(name)


def _operator(operator: str | Expr) -> Expr:
    if isinstance(operator, Expr):
        return operator
    if operator not in _RANGE_OPERATORS:
        message = f"unsupported range operator: {operator!r}"
        raise ValueError(message)
    return as_expr(operator, cast="xs:string")


def _depth(depth: str | Expr) -> Expr:
    if isinstance(depth, Expr):
        return depth
    if depth not in _DIRECTORY_DEPTHS:
        message = f"directory depth must be '1' or 'infinity': {depth!r}"
        raise ValueError(message)
    return as_expr(depth, cast="xs:string")


@experimental()
class Cts:
    """Pure ``cts:`` builders returning expression trees."""

    @staticmethod
    def and_query(queries, *, options=None) -> Expr:
        """Build ``cts:and-query``.

        Parameters
        ----------
        queries : Expr | list | tuple
            Query expression or sequence of query expressions.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:and-query", [queries], [options])

    @staticmethod
    def or_query(queries, *, options=None) -> Expr:
        """Build ``cts:or-query``.

        Parameters
        ----------
        queries : Expr | list | tuple
            Query expression or sequence of query expressions.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:or-query", [queries], [options])

    @staticmethod
    def not_query(query: Expr) -> Expr:
        """Build ``cts:not-query``.

        Parameters
        ----------
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:not-query", [query])

    @staticmethod
    def near_query(
        queries,
        *,
        distance=None,
        options=None,
        distance_weight=None,
    ) -> Expr:
        """Build ``cts:near-query``.

        Parameters
        ----------
        queries : Expr | list | tuple
            Query expression or sequence of query expressions.
        distance : int | float | Expr | None
            Maximum distance in words, cast to xs:double; None uses the native
            default.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        distance_weight : int | float | Expr | None
            Proximity scoring weight, cast to xs:double.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        distance_arg = xs.double(distance) if distance is not None else None
        return _FunctionCall(
            "cts:near-query",
            [queries],
            [distance_arg, options, _weight(distance_weight)],
        )

    @staticmethod
    def word_query(text, *, options=None, weight=None) -> Expr:
        """Build ``cts:word-query``.

        Parameters
        ----------
        text : str | Expr | list | tuple | None
            Text value or sequence; None is the empty sequence.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        weight : int | float | Expr | None
            Native query weight, cast to xs:double; None uses the server
            default.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:word-query",
            [text],
            [options, _weight(weight)],
        )

    @staticmethod
    def directory_query(uris, depth: str | Expr = "1") -> Expr:
        """Build ``cts:directory-query``; ``depth`` is ``"1"`` or ``"infinity"``.

        Parameters
        ----------
        uris : str | Expr | list | tuple
            URI value or sequence of URI values.
        depth : str | Expr
            Directory depth: "1" or "infinity", or an expression yielding one.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:directory-query",
            [uris, _depth(depth)],
        )

    @staticmethod
    def document_query(uris) -> Expr:
        """Build ``cts:document-query``.

        Parameters
        ----------
        uris : str | Expr | list | tuple
            URI value or sequence of URI values.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:document-query", [uris])

    @staticmethod
    def collection_query(uris) -> Expr:
        """Build ``cts:collection-query``.

        Parameters
        ----------
        uris : str | Expr | list | tuple
            URI value or sequence of URI values.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:collection-query", [uris])

    @staticmethod
    def document_root_query(name) -> Expr:
        """Build ``cts:document-root-query`` (MarkLogic 11+).

        Parameters
        ----------
        name : str | Expr
            One local name or QName expression, including xs.qname with a
            namespace URI.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:document-root-query", [_qname(name)])

    @staticmethod
    def element_value_query(element, text=None, *, options=None, weight=None) -> Expr:
        """Build ``cts:element-value-query``.

        Parameters
        ----------
        element : str | Expr | list | tuple
            Local name, QName expression, or a sequence of names for query
            builders.
        text : str | Expr | list | tuple | None
            Text value or sequence; None is the empty sequence.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        weight : int | float | Expr | None
            Native query weight, cast to xs:double; None uses the server
            default.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:element-value-query",
            [_qname(element), text],
            [options, _weight(weight)],
        )

    @staticmethod
    def element_word_query(element, text, *, options=None, weight=None) -> Expr:
        """Build ``cts:element-word-query``.

        Parameters
        ----------
        element : str | Expr | list | tuple
            Local name, QName expression, or a sequence of names for query
            builders.
        text : str | Expr | list | tuple | None
            Text value or sequence; None is the empty sequence.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        weight : int | float | Expr | None
            Native query weight, cast to xs:double; None uses the server
            default.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:element-word-query",
            [_qname(element), text],
            [options, _weight(weight)],
        )

    @staticmethod
    def element_range_query(
        element,
        operator,
        value,
        *,
        options=None,
        weight=None,
    ) -> Expr:
        """Build ``cts:element-range-query``.

        Parameters
        ----------
        element : str | Expr | list | tuple
            Local name, QName expression, or a sequence of names for query
            builders.
        operator : str | Expr
            Comparison operator (=, !=, <, <=, >, >=), or its expression.
        value : object
            Supported scalar or expression; query value parameters also accept
            sequences.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        weight : int | float | Expr | None
            Native query weight, cast to xs:double; None uses the server
            default.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:element-range-query",
            [_qname(element), _operator(operator), value],
            [options, _weight(weight)],
        )

    @staticmethod
    def path_range_query(path, operator, value, *, options=None, weight=None) -> Expr:
        """Build ``cts:path-range-query``.

        Parameters
        ----------
        path : str | Expr | list | tuple
            Index path value; path references require a single path.
        operator : str | Expr
            Comparison operator (=, !=, <, <=, >, >=), or its expression.
        value : object
            Supported scalar or expression; query value parameters also accept
            sequences.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        weight : int | float | Expr | None
            Native query weight, cast to xs:double; None uses the server
            default.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:path-range-query",
            [path, _operator(operator), value],
            [options, _weight(weight)],
        )

    @staticmethod
    def json_property_value_query(name, value, *, options=None, weight=None) -> Expr:
        """Build ``cts:json-property-value-query``.

        Parameters
        ----------
        name : str | Expr | list | tuple
            Native name argument; query builders accept a sequence of names.
        value : object
            Supported scalar or expression; query value parameters also accept
            sequences.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        weight : int | float | Expr | None
            Native query weight, cast to xs:double; None uses the server
            default.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:json-property-value-query",
            [name, value],
            [options, _weight(weight)],
        )

    @staticmethod
    def true_query() -> Expr:
        """Build ``cts:true-query``.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:true-query", [])

    @staticmethod
    def false_query() -> Expr:
        """Build ``cts:false-query``.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:false-query", [])

    @staticmethod
    def element_reference(element, *, options=None) -> Expr:
        """Build ``cts:element-reference``.

        Parameters
        ----------
        element : str | Expr
            One local name or QName expression, including xs.qname with a
            namespace URI.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:element-reference",
            [_qname(element)],
            [options],
        )

    @staticmethod
    def path_reference(path, *, options=None, namespaces=None) -> Expr:
        """Build ``cts:path-reference``.

        Parameters
        ----------
        path : str | Expr | list | tuple
            Index path value; path references require a single path.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        namespaces : Expr | None
            Expression producing a native map:map of namespace bindings, not a
            dict.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:path-reference",
            [path],
            [options, namespaces],
        )

    @staticmethod
    def json_property_reference(name, *, options=None) -> Expr:
        """Build ``cts:json-property-reference``.

        Parameters
        ----------
        name : str | Expr | list | tuple
            Native name argument; query builders accept a sequence of names.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:json-property-reference",
            [name],
            [options],
        )

    @staticmethod
    def field_reference(name, *, options=None) -> Expr:
        """Build ``cts:field-reference``.

        Parameters
        ----------
        name : str | Expr | list | tuple
            Native name argument; query builders accept a sequence of names.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:field-reference",
            [name],
            [options],
        )

    @staticmethod
    def collection_reference(*, options=None) -> Expr:
        """Build ``cts:collection-reference``.

        Parameters
        ----------
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:collection-reference", [], [options])

    @staticmethod
    def uri_reference() -> Expr:
        """Build ``cts:uri-reference``.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall("cts:uri-reference", [])

    @staticmethod
    def search(
        expression: Expr | None = None,
        query: Expr | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build ``cts:search`` over an Expr (default root); source needs ``xpath``.

        Parameters
        ----------
        expression : Expr | None
            Searchable node expression; None uses /. Wrap trusted source in
            xpath.
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:search",
            [xpath("/") if expression is None else search_path(expression), query],
            [
                options,
                _weight(quality_weight),
                forest_ids,
            ],
        )

    @staticmethod
    def uris(
        query: Expr | None = None,
        *,
        start: str | Expr | None = None,
        options=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build ``cts:uris`` over the URI lexicon.

        Parameters
        ----------
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:uris",
            [],
            [
                start,
                options,
                query,
                _weight(quality_weight),
                forest_ids,
            ],
        )

    @staticmethod
    def values(  # noqa: PLR0913 - native cts:values signature
        references,
        query: Expr | None = None,
        *,
        start=None,
        options=None,
        quality_weight=None,
        forest_ids=None,
    ) -> Expr:
        """Build ``cts:values`` over one or more range index references.

        Parameters
        ----------
        references : Expr | list | tuple
            One or more native range-index reference expressions.
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:values",
            [references],
            [
                start,
                options,
                query,
                _weight(quality_weight),
                forest_ids,
            ],
        )

    @staticmethod
    def estimate(
        query: Expr | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        maximum=None,
    ) -> Expr:
        """Build ``cts:estimate``.

        Parameters
        ----------
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        maximum : int | float | Expr | None
            Native maximum count; None leaves the count uncapped.

        Returns
        -------
        Expr
            Immutable expression; no request is sent until it is evaluated.
        """
        return _FunctionCall(
            "cts:estimate",
            [query],
            [
                options,
                _weight(quality_weight),
                forest_ids,
                _weight(maximum),
            ],
        )
