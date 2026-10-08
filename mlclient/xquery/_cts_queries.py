"""Native CTS queries that compile and serialize without performing I/O.

Build these objects with the cts singleton of mlclient.xquery. Serialization retains the
supplied arguments; MarkLogic applies database-dependent defaults, such as the
database language, when it reads the serialized query.
"""

from __future__ import annotations

import datetime
import json
import math
import re
from abc import ABC, abstractmethod
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, fields, replace
from decimal import Decimal
from io import StringIO
from typing import ClassVar, Literal
from xml.dom import minidom
from xml.etree.ElementTree import (
    Element,
    SubElement,
    TreeBuilder,
    XMLParser,
    iterparse,
    register_namespace,
)
from xml.parsers.expat import ExpatError

from mlclient.xquery.expressions import (
    AtomicValue,
    FunctionCall,
    NodeInput,
    ResultXPath,
    StringInput,
    XqyCompilationContext,
    XqyExpression,
    XqySequence,
    _as_expr,
    _as_qname,
)
from mlclient.search.base import SearchQuery

CTS_NS_URI = "http://marklogic.com/cts"
# ElementTree has no per-call prefix map; registering the prefix makes every
# serialized query read cts: instead of ns0:.
register_namespace("cts", CTS_NS_URI)
_SCIENTIFIC_WEIGHT_THRESHOLD = 0.000001
_XS_NS_URI = "http://www.w3.org/2001/XMLSchema"
_XSI_NS_URI = "http://www.w3.org/2001/XMLSchema-instance"
_QNAME_PREFIX = "q"
_QNAME_ARGUMENT_COUNT = 2
_JSON_RANGE_TYPES = {
    "xs:string": "string",
    "xs:integer": "decimal",
    "xs:decimal": "decimal",
    "xs:double": "double",
    "xs:float": "float",
    "xs:boolean": "boolean",
    "xs:date": "date",
    "xs:dateTime": "dateTime",
}
_UNQUOTED_CASTS = frozenset({"xs:integer", "xs:decimal", "xs:double", "xs:float"})
_DISPLAY_TRANSPARENT_CASTS = frozenset(
    {"xs:string", "xs:double", "xs:float", "xs:QName"},
)
__all__ = [
    "CTS_NS_URI",
    "AfterQuery",
    "AndNotQuery",
    "AndQuery",
    "BeforeQuery",
    "BoostQuery",
    "Box",
    "Circle",
    "CollectionQuery",
    "ColumnRangeQuery",
    "CtsQuery",
    "DirectoryQuery",
    "DocumentFormatQuery",
    "DocumentFragmentQuery",
    "DocumentPermissionQuery",
    "DocumentQuery",
    "DocumentRootQuery",
    "ElementAttributePairGeospatialQuery",
    "ElementAttributeRangeQuery",
    "ElementAttributeValueQuery",
    "ElementAttributeWordQuery",
    "ElementChildGeospatialQuery",
    "ElementGeospatialQuery",
    "ElementPairGeospatialQuery",
    "ElementQuery",
    "ElementRangeQuery",
    "ElementValueQuery",
    "ElementWordQuery",
    "FalseQuery",
    "FieldRangeQuery",
    "FieldValueQuery",
    "FieldWordQuery",
    "GeospatialRegionQuery",
    "JsonPropertyChildGeospatialQuery",
    "JsonPropertyGeospatialQuery",
    "JsonPropertyPairGeospatialQuery",
    "JsonPropertyRangeQuery",
    "JsonPropertyScopeQuery",
    "JsonPropertyValueQuery",
    "JsonPropertyWordQuery",
    "LocksFragmentQuery",
    "LsqtQuery",
    "NearQuery",
    "NotInQuery",
    "NotQuery",
    "OrQuery",
    "PathGeospatialQuery",
    "PathRangeQuery",
    "Period",
    "PeriodCompareQuery",
    "PeriodRangeQuery",
    "Point",
    "Polygon",
    "PropertiesFragmentQuery",
    "RangeQuery",
    "RegisteredQuery",
    "ReverseQuery",
    "RuntimeQuery",
    "SimilarQuery",
    "TripleRangeQuery",
    "TrueQuery",
    "WordQuery",
]


class _NativeCall(XqyExpression):
    """An immutable value compiled as one call of a native ``cts:`` function.

    Subclasses are frozen dataclasses whose fields hold the function's
    arguments in native order, as converted expressions. They compile to a
    call of ``_FUNCTION`` whose first ``_REQUIRED_ARGUMENTS`` fields are
    required arguments and the rest optional ones.
    """

    _FUNCTION: ClassVar[str]
    _REQUIRED_ARGUMENTS: ClassVar[int]

    def render(self, ctx: XqyCompilationContext) -> str:
        """Render the native constructor call.

        Parameters
        ----------
        ctx : XqyCompilationContext
            Shared compilation context.

        Returns
        -------
        str
            Native call with externally bound arguments.
        """
        arguments = self._native_arguments()
        return FunctionCall(
            self._FUNCTION,
            arguments[: self._REQUIRED_ARGUMENTS],
            arguments[self._REQUIRED_ARGUMENTS :],
        ).render(ctx)

    def _native_arguments(self) -> tuple[XqyExpression | None, ...]:
        """Return the native constructor's arguments in native order.

        Returns
        -------
        tuple[XqyExpression | None, ...]
            Every field's value; None marks an omitted optional argument.
        """
        return tuple(getattr(self, field.name) for field in fields(self))

    def __repr__(self) -> str:
        """Show the supplied arguments as literals, omitting unset ones.

        Returns
        -------
        str
            For example ``WordQuery(text='coffee', weight=2)``.
        """
        arguments = ", ".join(
            f"{field.name}={_display(getattr(self, field.name))}"
            for field in fields(self)
            if getattr(self, field.name) is not None
        )
        return f"{type(self).__name__}({arguments})"

    def _snapshot(self, **arguments: XqyExpression | None) -> None:
        """Store converted constructor arguments on this frozen query.

        Parameters
        ----------
        **arguments : XqyExpression | None
            Field names mapped to their converted values.
        """
        for name, value in arguments.items():
            object.__setattr__(self, name, value)


class CtsQuery(SearchQuery, _NativeCall):
    """A native CTS query supporting compilation and local serialization.

    Concrete queries compile as their native constructor call and serialize
    their literal arguments locally; serialization never evaluates arbitrary
    expressions.
    """

    def serialize(
        self,
        output_format: Literal["json", "xml"] = "json",
    ) -> dict | Element:
        """Build a fresh native representation in the selected format.

        Errors name where serialization failed: the native function, then for
        nested queries each enclosing one, and the argument.

        Parameters
        ----------
        output_format : {'json', 'xml'}, default 'json'
            Return a JSON-compatible dictionary or an ElementTree element.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh representation using the native CTS vocabulary.

        Raises
        ------
        ValueError
            For unsupported formats or literal values without a local form.
        TypeError
            For arguments requiring server evaluation.
        """
        with _error_context(self._error_label):
            return super().serialize(output_format)

    def __and__(self, other: CtsQuery) -> AndQuery:
        """Match both queries: ``a & b`` is ``cts.and_query([a, b])``.

        Parameters
        ----------
        other : CtsQuery
            The other query.

        Returns
        -------
        AndQuery
            The intersection; an and-query without options on the left is
            extended, so ``a & b & c`` holds all three queries.
        """
        if not isinstance(other, CtsQuery):
            return NotImplemented
        return AndQuery([*_operands(self, AndQuery), other])

    def __or__(self, other: CtsQuery) -> OrQuery:
        """Match either query: ``a | b`` is ``cts.or_query([a, b])``.

        Parameters
        ----------
        other : CtsQuery
            The other query.

        Returns
        -------
        OrQuery
            The union; an or-query without options on the left is extended,
            so ``a | b | c`` holds all three queries.
        """
        if not isinstance(other, CtsQuery):
            return NotImplemented
        return OrQuery([*_operands(self, OrQuery), other])

    def __invert__(self) -> NotQuery:
        """Match what this query does not: ``~a`` is ``cts.not_query(a)``.

        Returns
        -------
        NotQuery
            The negation.
        """
        return NotQuery(self)

    @property
    def _error_label(self) -> str:
        """Name this query in serialization errors.

        Returns
        -------
        str
            The native function, such as ``cts:word-query``.
        """
        return self._FUNCTION

    def to_combined_query(self) -> dict:
        """Wrap this CTS query in a JSON combined query.

        Returns
        -------
        dict
            ``{"search": {"ctsquery": ...}}`` holding the native CTS JSON.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For values that cannot be serialized locally.
        """
        return {"search": {"ctsquery": self.to_json()}}

    def _native(self, members: list[_Member], output_format) -> dict | Element:
        """Render this query's native element from its described fields.

        Parameters
        ----------
        members : list[_Member]
            Fields in native XML child order.
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native representation named after ``_FUNCTION``.
        """
        return _render(self._FUNCTION.removeprefix("cts:"), members, output_format)


class _Region(_NativeCall):
    """A literal geospatial region accepted by geospatial queries."""

    @property
    def region_type(self) -> str:
        """The native region type: point, box, circle or polygon.

        Returns
        -------
        str
            The local name of the region's ``cts:`` type.
        """
        return self._FUNCTION.removeprefix("cts:")

    @abstractmethod
    def to_text(self) -> str:
        """Return the region's native text form, as serialized queries hold it.

        It equals the region's string value in MarkLogic, such as ``10,20``
        for ``cts:point(10, 20)``.

        Returns
        -------
        str
            The region text.

        Raises
        ------
        TypeError
            For coordinates requiring server evaluation.
        """


@dataclass(frozen=True, init=False, repr=False)
class Box(_Region):
    """A native ``cts:box`` region between two latitudes and two longitudes.

    Build it with ``cts.box``; it compiles to the native constructor and
    serializes as ``[south, west, north, east]``.
    """

    _FUNCTION: ClassVar[str] = "cts:box"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 4

    south: XqyExpression
    west: XqyExpression
    north: XqyExpression
    east: XqyExpression

    def __init__(
        self,
        south: float | XqyExpression,
        west: float | XqyExpression,
        north: float | XqyExpression,
        east: float | XqyExpression,
    ):
        """Snapshot the box edges as doubles.

        The native signature declares xs:float edges, but MarkLogic keeps
        double precision; casting to xs:float would compile a different box
        (20.2 becomes 20.200001) than the one serialized locally.

        Parameters
        ----------
        south : float | XqyExpression
            Southern latitude.
        west : float | XqyExpression
            Western longitude.
        north : float | XqyExpression
            Northern latitude.
        east : float | XqyExpression
            Eastern longitude.
        """
        self._snapshot(
            south=_as_expr(south, cast="xs:double"),
            west=_as_expr(west, cast="xs:double"),
            north=_as_expr(north, cast="xs:double"),
            east=_as_expr(east, cast="xs:double"),
        )

    def to_text(self) -> str:
        """Return the native ``[south, west, north, east]`` text.

        Returns
        -------
        str
            Box text.

        Raises
        ------
        TypeError
            For edges requiring server evaluation.
        """
        edges = (self.south, self.west, self.north, self.east)
        return "[" + ", ".join(_coordinate(edge) for edge in edges) + "]"


@dataclass(frozen=True, init=False, repr=False)
class Circle(_Region):
    """A native ``cts:circle`` region: a radius around a center point.

    Build it with ``cts.circle``; it serializes as ``@radius latitude,longitude``.
    """

    _FUNCTION: ClassVar[str] = "cts:circle"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    radius: XqyExpression
    center: XqyExpression

    def __init__(self, radius: float | XqyExpression, center: XqyExpression):
        """Snapshot the radius as a native double and the center.

        Parameters
        ----------
        radius : float | XqyExpression
            Radius in the units of the query options (miles by default).
        center : XqyExpression
            The center point, usually a Point from ``cts.point``.
        """
        self._snapshot(
            radius=_as_expr(radius, cast="xs:double"),
            center=_as_expr(center),
        )

    def to_text(self) -> str:
        """Return the native ``@radius latitude,longitude`` text.

        Returns
        -------
        str
            Circle text.

        Raises
        ------
        TypeError
            For a radius or center requiring server evaluation.
        """
        return f"@{_coordinate(self.radius)} {_point_text(self.center)}"


@dataclass(frozen=True, init=False, repr=False)
class Period(_NativeCall):
    """A native ``cts:period`` between two date-times.

    Build it with ``cts.period``; it compiles to the native constructor and
    serializes as its start and end.
    """

    _FUNCTION: ClassVar[str] = "cts:period"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    start: XqyExpression
    end: XqyExpression

    def __init__(
        self,
        start: datetime.datetime | XqyExpression,
        end: datetime.datetime | XqyExpression,
    ):
        """Snapshot the period bounds.

        Parameters
        ----------
        start : datetime.datetime | XqyExpression
            Start of the period.
        end : datetime.datetime | XqyExpression
            End of the period.
        """
        self._snapshot(start=_as_expr(start), end=_as_expr(end))


@dataclass(frozen=True, init=False, repr=False)
class Point(_Region):
    """A native ``cts:point``, given as coordinates or as WKT text.

    Build it with ``cts.point``; coordinates serialize as ``latitude,longitude``,
    while a WKT point requires server evaluation.
    """

    _FUNCTION: ClassVar[str] = "cts:point"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    latitude_or_wkt: XqyExpression
    longitude: XqyExpression | None

    def __init__(
        self,
        latitude_or_wkt: float | str | XqyExpression,
        longitude: float | XqyExpression | None = None,
    ):
        """Snapshot the coordinates or the WKT text.

        Parameters
        ----------
        latitude_or_wkt : float | str | XqyExpression
            Latitude, or the point as well-known text without a longitude.
        longitude : float | XqyExpression | None, default None
            Longitude; omitted for a WKT point.
        """
        self._snapshot(
            latitude_or_wkt=_as_expr(latitude_or_wkt),
            longitude=_optional(longitude),
        )

    def to_text(self) -> str:
        """Return the native ``latitude,longitude`` text.

        Returns
        -------
        str
            Point text.

        Raises
        ------
        TypeError
            For a WKT point or coordinates requiring server evaluation.
        """
        if self.longitude is None:
            message = "CTS point given as WKT text requires server evaluation."
            raise TypeError(message)
        return f"{_coordinate(self.latitude_or_wkt)},{_coordinate(self.longitude)}"


@dataclass(frozen=True, init=False, repr=False)
class Polygon(_Region):
    """A native ``cts:polygon`` region bounded by points or given as WKT text.

    Build it with ``cts.polygon``; points serialize as space-separated
    ``latitude,longitude`` vertices.
    """

    _FUNCTION: ClassVar[str] = "cts:polygon"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    vertices: XqyExpression

    def __init__(self, vertices: str | XqyExpression):
        """Snapshot the vertices.

        Parameters
        ----------
        vertices : str | XqyExpression
            Points in order, the first repeated last to close the polygon, or
            the polygon as well-known text.
        """
        self._snapshot(vertices=_as_expr(vertices))

    def to_text(self) -> str:
        """Return the native space-separated vertex text.

        Returns
        -------
        str
            Polygon text.

        Raises
        ------
        TypeError
            For WKT text or vertices requiring server evaluation.
        """
        if isinstance(self.vertices, AtomicValue):
            message = "CTS polygon given as WKT text requires server evaluation."
            raise TypeError(message)
        return " ".join(_point_text(vertex) for vertex in _sequence(self.vertices))


@dataclass(frozen=True, init=False, repr=False)
class AfterQuery(CtsQuery):
    """Compile and serialize native ``cts:after-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:after-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    timestamp: XqyExpression

    def __init__(
        self,
        timestamp: int | XqyExpression,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        timestamp : int | XqyExpression
            A commit timestamp. Database fragments committed after this timestamp are
            matched.
        """
        self._snapshot(
            timestamp=_as_expr(timestamp),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _lexical_member("timestamp", "timestamp", self.timestamp),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class AndNotQuery(CtsQuery):
    """Compile and serialize native ``cts:and-not-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:and-not-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    positive_query: XqyExpression
    negative_query: XqyExpression

    def __init__(self, positive_query: StringInput, negative_query: StringInput):
        """Snapshot constructor arguments.

        Parameters
        ----------
        positive_query : str | XqyExpression
            A positive query, specifying the search results filtered in.
        negative_query : str | XqyExpression
            A negative query, specifying the search results to filter out.
        """
        self._snapshot(
            positive_query=_as_expr(positive_query),
            negative_query=_as_expr(negative_query),
        )

    def _serialize(self, output_format):
        """Serialize the positive and negative queries in native wrappers.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [
                _WrappedQueryMember("positiveQuery", "positive", self.positive_query),
                _WrappedQueryMember("negativeQuery", "negative", self.negative_query),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class AndQuery(CtsQuery):
    """Intersect subqueries using the native CTS constructor."""

    _FUNCTION: ClassVar[str] = "cts:and-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    queries: XqyExpression
    options: XqyExpression | None

    def __init__(self, queries: StringInput, *, options: StringInput = None):
        """Snapshot the subqueries and optional ordering flags.

        Parameters
        ----------
        queries : StringInput
            Subqueries or strings implicitly converted by MarkLogic to word queries.
        options : StringInput, default None
            Native and-query options.
        """
        self._snapshot(
            queries=_as_expr(queries),
            options=_choice_options_argument(options, _ORDER_OPTIONS, "and-query"),
        )

    def _serialize(self, output_format):
        """Serialize the intersection with native child-query cardinality.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        ValueError
            For options other than one of ordered or unordered.
        """
        options = _strings(self.options)
        _check_choice_options(options, _ORDER_OPTIONS, "and-query")
        return self._native(
            [
                _QueriesMember("queries", "", _sequence(self.queries)),
                _TextsMember("options", "option", options),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class BeforeQuery(CtsQuery):
    """Compile and serialize native ``cts:before-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:before-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    timestamp: XqyExpression

    def __init__(
        self,
        timestamp: int | XqyExpression,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        timestamp : int | XqyExpression
            A commit timestamp. Database fragments committed before this timestamp are
            matched.
        """
        self._snapshot(
            timestamp=_as_expr(timestamp),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _lexical_member("timestamp", "timestamp", self.timestamp),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class BoostQuery(CtsQuery):
    """Compile and serialize native ``cts:boost-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:boost-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    matching_query: XqyExpression
    boosting_query: XqyExpression

    def __init__(self, matching_query: StringInput, boosting_query: StringInput):
        """Snapshot constructor arguments.

        Parameters
        ----------
        matching_query : str | XqyExpression
            A sub-query that is used for match and scoring.
        boosting_query : str | XqyExpression
            A sub-query that is used only for boosting score.
        """
        self._snapshot(
            matching_query=_as_expr(matching_query),
            boosting_query=_as_expr(boosting_query),
        )

    def _serialize(self, output_format):
        """Serialize the matching and boosting queries in native wrappers.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [
                _WrappedQueryMember(
                    "matchingQuery",
                    "matching-query",
                    self.matching_query,
                ),
                _WrappedQueryMember(
                    "boostingQuery",
                    "boosting-query",
                    self.boosting_query,
                ),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class CollectionQuery(CtsQuery):
    """Select documents belonging to any of the given collections."""

    _FUNCTION: ClassVar[str] = "cts:collection-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    uris: XqyExpression

    def __init__(self, uris: StringInput):
        """Snapshot collection URIs while retaining expression composition.

        Parameters
        ----------
        uris : StringInput
            Collection URIs or an expression evaluated by MarkLogic.
        """
        self._snapshot(
            uris=_as_expr(uris),
        )

    def _serialize(self, output_format):
        """Serialize the collection URIs.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [_texts_member("uris", "uri", self.uris)],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ColumnRangeQuery(CtsQuery):
    """Compile a native column query requiring database metadata to serialize.

    MarkLogic lowers this constructor to a triple-range query containing a TDE
    column ID. Supply that metadata with ``with_column_id`` before serializing;
    constructing, compiling and serializing never fetch it implicitly.
    """

    _FUNCTION: ClassVar[str] = "cts:column-range-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 4

    schema: XqyExpression
    view: XqyExpression
    column: XqyExpression
    value: XqyExpression
    operator: XqyExpression | None
    options: XqyExpression | None
    weight: XqyExpression | None
    column_id: int | None

    def __init__(
        self,
        schema: str | XqyExpression,
        view: str | XqyExpression,
        column: str | XqyExpression,
        value: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        operator: str | XqyExpression | None = None,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
        column_id: int | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        schema : str | XqyExpression
            The TDE schema name.
        view : str | XqyExpression
            The TDE view name.
        column : str | XqyExpression
            The TDE column name.
        value : AtomicInput
            One or more values used for querying.
        operator : str | XqyExpression | None, optional
            Operator for the $value values. The default operator is "=". Operators
            include: "<" Match range index values less than $value. "<=" Match range
            index values less than or equal to $value. ">" Match range index values
            greater than $value. ">=" Match range index values greater than or equal to
            $value. "=" Match range index values equal to $value. "!=" Match range index
            values not equal to $value.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "score-function= function " Use the
            selected scoring function. The score function may be: linear Use a linear
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        column_id : int or None, optional
            Destination TDE column ID used only for local serialization.
        """
        if column_id is not None and (
            isinstance(column_id, bool)
            or not isinstance(column_id, int)
            or not 0 <= column_id < 2**64
        ):
            message = "CTS column ID must be an unsigned 64-bit integer."
            raise ValueError(message)
        self._snapshot(
            schema=_as_expr(schema),
            view=_as_expr(view),
            column=_as_expr(column),
            value=_as_expr(value),
            operator=_operator_argument(operator, required=False),
            options=_optional(options),
            weight=_optional_double(weight),
            column_id=column_id,
        )

    def _native_arguments(self) -> tuple[XqyExpression | None, ...]:
        """Return the native arguments; the column ID only serves serialization.

        Returns
        -------
        tuple[XqyExpression | None, ...]
            Every field's value except the column ID.
        """
        return tuple(
            getattr(self, field.name)
            for field in fields(self)
            if field.name != "column_id"
        )

    def with_column_id(self, column_id: int) -> ColumnRangeQuery:
        """Return a new query with explicit destination column metadata.

        Parameters
        ----------
        column_id : int
            Unsigned 64-bit ID obtained from the destination's native column query.

        Returns
        -------
        ColumnRangeQuery
            Independently serializable query with unchanged XQuery compilation.

        Raises
        ------
        ValueError
            If the ID is not an unsigned 64-bit integer.
        """
        return replace(self, column_id=column_id)

    def _serialize(self, output_format):
        """Serialize as the native triple-range query over the TDE column.

        MarkLogic stores a column range query as a triple-range query whose
        predicate names the column and its ID.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native triple-range query.

        Raises
        ------
        TypeError
            Without a column ID, or for arguments requiring server evaluation.
        """
        if self.column_id is None:
            message = (
                "CTS column serialization requires the destination database's "
                "TDE column ID; use with_column_id()."
            )
            raise TypeError(message)
        name = ".".join(
            _single(_strings(value)) for value in (self.schema, self.view, self.column)
        )
        return _render(
            "triple-range-query",
            [
                *_triple_operators(self.operator),
                _ColumnMember("predicate", "predicate", (name, self.column_id)),
                _triples_member("object", self.value),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class DirectoryQuery(CtsQuery):
    """Compile and serialize native ``cts:directory-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:directory-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    uris: XqyExpression
    depth: XqyExpression | None

    def __init__(self, uris: StringInput, depth: StringInput = "1"):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        uris : StringInput
            One or more directory URIs.
        depth : str | XqyExpression | None, optional
            "1" for immediate children, "infinity" for all. If not supplied, depth is
            "1".
        """
        self._snapshot(
            uris=_as_expr(uris),
            depth=_depth_argument(depth),
        )

    def _serialize(self, output_format):
        """Serialize the directory URIs and a non-default depth.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        ValueError
            For a depth expression holding a value other than 1 or infinity.
        """
        depths = _strings(self.depth)
        if len(depths) > 1 or any(depth not in _DIRECTORY_DEPTHS for depth in depths):
            message = f"depth {depths!r} must be '1' or 'infinity'"
            raise ValueError(message)
        return self._native(
            [
                _texts_member("uris", "uri", self.uris),
                _AttributeMember(
                    "depth",
                    "depth",
                    "infinity" if depths == ["infinity"] else None,
                ),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class DocumentFormatQuery(CtsQuery):
    """Compile and serialize native ``cts:document-format-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:document-format-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    format: XqyExpression

    def __init__(
        self,
        format: str | XqyExpression,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        format : str | XqyExpression
            Case insensitve one of: "json","xml","text","binary". This will result in a
            XDMP-ARG exception in case of an invalid format.
        """
        self._snapshot(
            format=_as_expr(format),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _attribute_member("format", "format", self.format),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class DocumentFragmentQuery(CtsQuery):
    """Compile and serialize native ``cts:document-fragment-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:document-fragment-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    query: XqyExpression

    def __init__(self, query: StringInput):
        """Snapshot constructor arguments.

        Parameters
        ----------
        query : str | XqyExpression
            A query to be matched against any document fragment.
        """
        self._snapshot(
            query=_as_expr(query),
        )

    def _serialize(self, output_format):
        """Serialize the nested query.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [_query_member("query", "query", self.query)],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class DocumentPermissionQuery(CtsQuery):
    """Compile and serialize native ``cts:document-permission-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:document-permission-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    role: XqyExpression
    capability: XqyExpression

    def __init__(
        self,
        role: str | XqyExpression,
        capability: str | XqyExpression,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        role : str | XqyExpression
            The role of the permission
        capability : str | XqyExpression
            The capability of the permission (read, update, node-update, insert,
            execute)
        """
        self._snapshot(
            role=_as_expr(role),
            capability=_as_expr(capability),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _attribute_member("role", "role", self.role),
                _attribute_member("capability", "capability", self.capability),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class DocumentQuery(CtsQuery):
    """Compile and serialize native ``cts:document-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:document-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    uris: XqyExpression

    def __init__(self, uris: StringInput):
        """Snapshot constructor arguments.

        Parameters
        ----------
        uris : StringInput
            One or more document URIs.
        """
        self._snapshot(
            uris=_as_expr(uris),
        )

    def _serialize(self, output_format):
        """Serialize the document URIs.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [_texts_member("uris", "uri", self.uris)],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class DocumentRootQuery(CtsQuery):
    """Compile and serialize native ``cts:document-root-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:document-root-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    root: XqyExpression

    def __init__(
        self,
        root: str | XqyExpression,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        root : str | XqyExpression
            The root QName to query.
        """
        self._snapshot(
            root=_as_qname(root),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qname_member("root", "root", self.root),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementAttributePairGeospatialQuery(CtsQuery):
    """Compile and serialize this native query.

    Native constructor: ``cts:element-attribute-pair-geospatial-query``.
    """

    _FUNCTION: ClassVar[str] = "cts:element-attribute-pair-geospatial-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 4

    element_name: XqyExpression
    latitude_attribute_names: XqyExpression
    longitude_attribute_names: XqyExpression
    regions: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        element_name: StringInput,
        latitude_attribute_names: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        longitude_attribute_names: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        regions: XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more parent element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches.
        latitude_attribute_names : StringInput
            One or more latitude attribute QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching latitude attribute in any point instance will be checked.
        longitude_attribute_names : StringInput
            One or more longitude attribute QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching longitude attribute in any point instance will be checked.
        regions : XqyExpression | list[XqyExpression] | None
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            latitude_attribute_names=_as_qname(latitude_attribute_names),
            longitude_attribute_names=_as_qname(longitude_attribute_names),
            regions=_as_expr(regions),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _qnames_member(
                    "latitudeAttribute",
                    "latitude",
                    self.latitude_attribute_names,
                ),
                _qnames_member(
                    "longitudeAttribute",
                    "longitude",
                    self.longitude_attribute_names,
                ),
                _regions_member("region", "region", self.regions),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementAttributeRangeQuery(CtsQuery):
    """Compile and serialize native ``cts:element-attribute-range-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-attribute-range-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 4

    element_name: XqyExpression
    attribute_name: XqyExpression
    operator: XqyExpression
    value: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        element_name: StringInput,
        attribute_name: StringInput,
        operator: str | XqyExpression,
        value: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        attribute_name : StringInput
            One or more attribute QNames to match. When multiple QNames are specified,
            the query matches if any QName matches.
        operator : str | XqyExpression
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : AtomicInput
            Some values to match. When multiple values are specified, the query matches
            if any value matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            attribute_name=_as_qname(attribute_name),
            operator=_operator_argument(operator),
            value=_as_expr(value),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _qnames_member("attribute", "attribute", self.attribute_name),
                _attribute_member("operator", "operator", self.operator),
                _typed_member("value", "value", self.value),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementAttributeValueQuery(CtsQuery):
    """Compile and serialize native ``cts:element-attribute-value-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-attribute-value-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    element_name: XqyExpression
    attribute_name: XqyExpression
    text: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        element_name: StringInput,
        attribute_name: StringInput,
        text: StringInput,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        attribute_name : StringInput
            One or more attribute QNames to match. When multiple QNames are specified,
            the query matches if any QName matches.
        text : StringInput
            One or more attribute values to match. When multiple strings are specified,
            the query matches if any string matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "min-occurs= number " Specifies the minimum number of
            occurrences required. If fewer that this number of words occur, the fragment
            does not match. The default is 1. "max-occurs= number " Specifies the
            maximum number of occurrences required. If more than this number of words
            occur, the fragment does not match. The default is unbounded. "synonym"
            Specifies that all of the terms in the $text parameter are considered
            synonyms for scoring purposes. The result is that occurrences of more than
            one of the synonyms are scored as if there are more occurrences of the same
            term (as opposed to having a separate term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            attribute_name=_as_qname(attribute_name),
            text=_as_expr(text),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _qnames_member("attribute", "attribute", self.attribute_name),
                _texts_member("text", "text", self.text),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementAttributeWordQuery(CtsQuery):
    """Compile and serialize native ``cts:element-attribute-word-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-attribute-word-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    element_name: XqyExpression
    attribute_name: XqyExpression
    text: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        element_name: StringInput,
        attribute_name: StringInput,
        text: StringInput,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        attribute_name : StringInput
            One or more attribute QNames to match. When multiple QNames are specified,
            the query matches if any QName matches.
        text : StringInput
            Some words or phrases to match. When multiple strings are specified, the
            query matches if any string matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "min-occurs= number " Specifies the minimum number of
            occurrences required. If fewer that this number of words occur, the fragment
            does not match. The default is 1. "max-occurs= number " Specifies the
            maximum number of occurrences required. If more than this number of words
            occur, the fragment does not match. The default is unbounded. "synonym"
            Specifies that all of the terms in the $text parameter are considered
            synonyms for scoring purposes. The result is that occurrences of more than
            one of the synonyms are scored as if there are more occurrences of the same
            term (as opposed to having a separate term that contributes to score).
            "lexicon-expand= value " The value is one of full , prefix-postfix , off ,
            or heuristic (the default is heuristic ). An option with a value of
            lexicon-expand=full specifies that wildcards are resolved by expanding the
            pattern to words in a lexicon (if there is one available), and turning into
            a series of cts:word-queries , even if this takes a long time to evaluate.
            An option with a value of lexicon-expand=prefix-postfix specifies that
            wildcards are resolved by expanding the pattern to the pre- and postfixes of
            the words in the word lexicon (if there is one), and turning the query into
            a series of character queries, even if it takes a long time to evaluate. An
            option with a value of lexicon-expand=off specifies that wildcards are only
            resolved by looking up character patterns in the search pattern index, not
            in the lexicon. An option with a value of lexicon-expand=heuristic , which
            is the default, specifies that wildcards are resolved by using a series of
            internal rules, such as estimating the number of lexicon entries that need
            to be scanned, seeing if the estimate crosses certain thresholds, and (if
            appropriate), using another way besides lexicon expansion to resolve the
            query. * "lexicon-expansion-limit= number " Specifies the limit for lexicon
            expansion. This puts a restriction on the number of lexicon expansions that
            can be performed. If the limit is exceeded, the server may raise an error
            depending on whether the "limit-check" option is set. The default value for
            this option will be 4096. "limit-check" Specifies that an error will be
            raised if the lexicon expansion exceeds the specified limit.
            "no-limit-check" Specifies that error will not be raised if the lexicon
            expansion exceeds the specified limit. The server will try to resolve the
            wildcard.
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            attribute_name=_as_qname(attribute_name),
            text=_as_expr(text),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _qnames_member("attribute", "attribute", self.attribute_name),
                _texts_member("text", "text", self.text),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementChildGeospatialQuery(CtsQuery):
    """Compile and serialize native ``cts:element-child-geospatial-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-child-geospatial-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    parent_element_name: XqyExpression
    child_element_names: XqyExpression
    regions: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        parent_element_name: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        child_element_names: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        regions: XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        parent_element_name : StringInput
            One or more parent element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches.
        child_element_names : StringInput
            One or more child element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching latitude child in any point instance will be checked. The element
            must specify both latitude and longitude coordinates.
        regions : XqyExpression | list[XqyExpression] | None
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= string " Use the coordinate system at the
            given precision. Allowed values: float (default) and double . "units= value
            " Measure distance and the radii of circles in the specified units. Allowed
            values: miles (default), km , feet , meters . "boundaries-included" Points
            on boxes', circles', and polygons' boundaries are counted as matching. This
            is the default. "boundaries-excluded" Points on boxes', circles', and
            polygons' boundaries are not counted as matching.
            "boundaries-latitude-excluded" Points on boxes' latitude boundaries are not
            counted as matching. "boundaries-longitude-excluded" Points on boxes'
            longitude boundaries are not counted as matching.
            "boundaries-south-excluded" Points on the boxes' southern boundaries are not
            counted as matching. "boundaries-west-excluded" Points on the boxes' western
            boundaries are not counted as matching. "boundaries-north-excluded" Points
            on the boxes' northern boundaries are not counted as matching.
            "boundaries-east-excluded" Points on the boxes' eastern boundaries are not
            counted as matching. "boundaries-circle-excluded" Points on circles'
            boundary are not counted as matching. "boundaries-endpoints-excluded" Points
            on linestrings' boundary (the endpoints) are not counted as matching.
            "cached" Cache the results of this query in the list cache. "uncached" Do
            not cache the results of this query in the list cache. "type=long-lat-point"
            Specifies the format for the point in the data as longitude first, latitude
            second. "type=point" Specifies the format for the point in the data as
            latitude first, longitude second. This is the default format.
            "score-function= function " Use the selected scoring function. The score
            function may be: linear Use a linear function of the difference between the
            specified query value and the matching value in the index to calculate a
            score for this range query. reciprocal Use a reciprocal function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. zero This range query does
            not contribute to the score. This is the default. "slope-factor= number "
            Apply the given number as a scaling factor to the slope of the scoring
            function. The default is 1.0. "synonym" Specifies that all of the terms in
            the $regions parameter are considered synonyms for scoring purposes. The
            result is that occurrences of more than one of the synonyms are scored as if
            there are more occurrence of the same term (as opposed to having a separate
            term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            parent_element_name=_as_qname(parent_element_name),
            child_element_names=_as_qname(child_element_names),
            regions=_as_expr(regions),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.parent_element_name),
                _qnames_member("child", "child", self.child_element_names),
                _regions_member("region", "region", self.regions),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementGeospatialQuery(CtsQuery):
    """Compile and serialize native ``cts:element-geospatial-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-geospatial-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    element_name: XqyExpression
    regions: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        element_name: StringInput,
        regions: XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        regions : XqyExpression | list[XqyExpression] | None
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "type=long-lat-point" Specifies the format for the point
            in the data as longitude first, latitude second. "type=point" Specifies the
            format for the point in the data as latitude first, longitude second. This
            is the default format. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            regions=_as_expr(regions),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _regions_member("region", "region", self.regions),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementPairGeospatialQuery(CtsQuery):
    """Compile and serialize native ``cts:element-pair-geospatial-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-pair-geospatial-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 4

    element_name: XqyExpression
    latitude_element_names: XqyExpression
    longitude_element_names: XqyExpression
    regions: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        element_name: StringInput,
        latitude_element_names: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        longitude_element_names: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        regions: XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more parent element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches.
        latitude_element_names : StringInput
            One or more latitude element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching latitude child in any point instance will be checked.
        longitude_element_names : StringInput
            One or more longitude element QNames to match. When multiple QNames are
            specified, the query matches if any QName matches; however, only the first
            matching longitude child in any point instance will be checked.
        regions : XqyExpression | list[XqyExpression] | None
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            latitude_element_names=_as_qname(latitude_element_names),
            longitude_element_names=_as_qname(longitude_element_names),
            regions=_as_expr(regions),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _qnames_member("latitude", "latitude", self.latitude_element_names),
                _qnames_member("longitude", "longitude", self.longitude_element_names),
                _regions_member("region", "region", self.regions),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementQuery(CtsQuery):
    """Compile and serialize native ``cts:element-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    element_name: XqyExpression
    query: XqyExpression

    def __init__(
        self,
        element_name: StringInput,
        query: str | XqyExpression,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        query : str | XqyExpression
            A query for the element to match. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            query=_as_expr(query),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _query_member("query", "query", self.query),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementRangeQuery(CtsQuery):
    """Compile and serialize native ``cts:element-range-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-range-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    element_name: XqyExpression
    operator: XqyExpression
    value: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        element_name: StringInput,
        operator: str | XqyExpression,
        value: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        operator : str | XqyExpression
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : AtomicInput
            One or more element values to match. When multiple values are specified, the
            query matches if any value matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            operator=_operator_argument(operator),
            value=_as_expr(value),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _attribute_member("operator", "operator", self.operator),
                _typed_member("value", "value", self.value),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementValueQuery(CtsQuery):
    """Compile and serialize native ``cts:element-value-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-value-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    element_name: XqyExpression
    text: XqyExpression | None
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        element_name: StringInput,
        *,
        text: StringInput = None,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        text : StringInput, optional
            One or more element values to match. When multiple strings are specified,
            the query matches if any string matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "min-occurs= number " Specifies the minimum number of
            occurrences required. If fewer that this number of words occur, the fragment
            does not match. The default is 1. "max-occurs= number " Specifies the
            maximum number of occurrences required. If more than this number of words
            occur, the fragment does not match. The default is unbounded. "synonym"
            Specifies that all of the terms in the $text parameter are considered
            synonyms for scoring purposes. The result is that occurrences of more than
            one of the synonyms are scored as if there are more occurrences of the same
            term (as opposed to having a separate term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            text=_optional(text),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _value_texts_member("text", "text", self.text),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ElementWordQuery(CtsQuery):
    """Compile and serialize native ``cts:element-word-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:element-word-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    element_name: XqyExpression
    text: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        element_name: StringInput,
        text: StringInput,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        element_name : StringInput
            One or more element QNames to match. When multiple QNames are specified, the
            query matches if any QName matches.
        text : StringInput
            Some words or phrases to match. When multiple strings are specified, the
            query matches if any string matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "distance-weight= number " A weight applied based on the
            minimum distance between matches of this query. Higher weights add to the
            importance of proximity (as opposed to term matches) when the relevance
            order is calculated. The default value is 0.0 (no impact of proximity). The
            weight should be between 64 and -16. Weights greater than 64 will have the
            same effect as a weight of 64. This parameter has no effect if the word
            positions index is not enabled. This parameter has no effect on searches
            that use score-simple, score-random, or score-zero (because those scoring
            algorithms do not consider term frequency, proximity is irrelevant).
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "synonym" Specifies that all of
            the terms in the $text parameter are considered synonyms for scoring
            purposes. The result is that occurrences of more than one of the synonyms
            are scored as if there are more occurrences of the same term (as opposed to
            having a separate term that contributes to score). "lexicon-expand= value "
            The value is one of full , prefix-postfix , off , or heuristic (the default
            is heuristic ). An option with a value of lexicon-expand=full specifies that
            wildcards are resolved by expanding the pattern to words in a lexicon (if
            there is one available), and turning into a series of cts:word-queries ,
            even if this takes a long time to evaluate. An option with a value of
            lexicon-expand=prefix-postfix specifies that wildcards are resolved by
            expanding the pattern to the pre- and postfixes of the words in the word
            lexicon (if there is one), and turning the query into a series of character
            queries, even if it takes a long time to evaluate. An option with a value of
            lexicon-expand=off specifies that wildcards are only resolved by looking up
            character patterns in the search pattern index, not in the lexicon. An
            option with a value of lexicon-expand=heuristic , which is the default,
            specifies that wildcards are resolved by using a series of internal rules,
            such as estimating the number of lexicon entries that need to be scanned,
            seeing if the estimate crosses certain thresholds, and (if appropriate),
            using another way besides lexicon expansion to resolve the query.
            "lexicon-expansion-limit= number " Specifies the limit for lexicon
            expansion. This puts a restriction on the number of lexicon expansions that
            can be performed. If the limit is exceeded, the server may raise an error
            depending on whether the "limit-check" option is set. The default value for
            this option will be 4096. "limit-check" Specifies that an error will be
            raised if the lexicon expansion exceeds the specified limit.
            "no-limit-check" Specifies that error will not be raised if the lexicon
            expansion exceeds the specified limit. The server will try to resolve the
            wildcard. "no-limit-check" is default, if neither "limit-check" nor
            "no-limit-check" is explicitly specified.
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            element_name=_as_qname(element_name),
            text=_as_expr(text),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _qnames_member("element", "element", self.element_name),
                _texts_member("text", "text", self.text),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, repr=False)
class FalseQuery(CtsQuery):
    """Compile and serialize native ``cts:false-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:false-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 0

    def _serialize(self, output_format):
        """Serialize the query, which has no arguments.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native([], output_format)


@dataclass(frozen=True, init=False, repr=False)
class FieldRangeQuery(CtsQuery):
    """Compile and serialize native ``cts:field-range-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:field-range-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    field_name: XqyExpression
    operator: XqyExpression
    value: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        field_name: StringInput,
        operator: str | XqyExpression,
        value: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        field_name : StringInput
            One or more field names to match. When multiple field names are specified,
            the query matches if any field name matches.
        operator : str | XqyExpression
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : AtomicInput
            One or more field values to match. When multiple values are specified, the
            query matches if any value matches. The value must be a type for which there
            is a range index defined.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            field_name=_as_expr(field_name),
            operator=_operator_argument(operator),
            value=_as_expr(value),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member("field", "field", self.field_name),
                _attribute_member("operator", "operator", self.operator),
                _typed_member("value", "value", self.value),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class FieldValueQuery(CtsQuery):
    """Compile and serialize native ``cts:field-value-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:field-value-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    field_name: XqyExpression
    text: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        field_name: StringInput,
        text: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        field_name : StringInput
            One or more field names to search over. If multiple field names are
            supplied, the match can be in any of the specified fields (or-query
            semantics).
        text : AtomicInput
            The values to match. If multiple values are specified, the query matches if
            any of the values match (or-query semantics). For XML and metadata, the
            values should be strings. For JSON, the values can be strings, numbers or
            booleans to match correspondingly typed nodes. To match null, pass in the
            empty sequence.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "distance-weight= number " A weight applied based on the
            minimum distance between matches of this query. Higher weights add to the
            importance of proximity (as opposed to term matches) when the relevance
            order is calculated. The default value is 0.0 (no impact of proximity). The
            weight should be between 64 and -16. Weights greater than 64 will have the
            same effect as a weight of 64. This parameter has no effect if the word
            positions index is not enabled. This parameter has no effect on searches
            that use score-simple or score-random (because those scoring algorithms do
            not consider term frequency, proximity is irrelevant). "min-occurs= number "
            Specifies the minimum number of occurrences required. If fewer that this
            number of words occur, the fragment does not match. The default is 1.
            "max-occurs= number " Specifies the maximum number of occurrences required.
            If more than this number of words occur, the fragment does not match. The
            default is unbounded. "synonym" Specifies that all of the terms in the $text
            parameter are considered synonyms for scoring purposes. The result is that
            occurrences of more than one of the synonyms are scored as if there are more
            occurrences of the same term (as opposed to having a separate term that
            contributes to score). "lexicon-expansion-limit= number " Specifies the
            limit for lexicon expansion. This puts a restriction on the number of
            lexicon expansions that can be performed. If the limit is exceeded, the
            server may raise an error depending on whether the "limit-check" option is
            set. The default value for this option will be 4096. "limit-check" Specifies
            that an error will be raised if the lexicon expansion exceeds the specified
            limit. "no-limit-check" Specifies that error will not be raised if the
            lexicon expansion exceeds the specified limit. The server will try to
            resolve the wildcard.
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            field_name=_as_expr(field_name),
            text=_as_expr(text),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member("field", "field", self.field_name),
                _texts_member("text", "text", self.text),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class FieldWordQuery(CtsQuery):
    """Compile and serialize native ``cts:field-word-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:field-word-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    field_name: XqyExpression
    text: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        field_name: StringInput,
        text: StringInput,
        *,
        options=None,
        weight=None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        field_name : StringInput
            One or more field names to search over. If multiple field names are
            supplied, the match can be in any of the specified fields (or-query
            semantics).
        text : StringInput
            The word or phrase to match. If multiple strings are specified, the query
            matches if any of the words or phrases match (or-query semantics).
        options : StringInput, optional
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "distance-weight= number " A weight applied based on the
            minimum distance between matches of this query. Higher weights add to the
            importance of proximity (as opposed to term matches) when the relevance
            order is calculated. The default value is 0.0 (no impact of proximity). The
            weight should be between 64 and -16. Weights greater than 64 will have the
            same effect as a weight of 64. This parameter has no effect if the word
            positions index is not enabled. This parameter has no effect on searches
            that use score-simple, score-random, or score-zero (because those scoring
            algorithms do not consider term frequency, proximity is irrelevant).
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "synonym" Specifies that all of
            the terms in the $text parameter are considered synonyms for scoring
            purposes. The result is that occurrences of more than one of the synonyms
            are scored as if there are more occurrences of the same term (as opposed to
            having a separate term that contributes to score). "lexicon-expand= value "
            The value is one of full , prefix-postfix , off , or heuristic (the default
            is heuristic ). An option with a value of lexicon-expand=full specifies that
            wildcards are resolved by expanding the pattern to words in a lexicon (if
            there is one available), and turning into a series of cts:word-queries ,
            even if this takes a long time to evaluate. An option with a value of
            lexicon-expand=prefix-postfix specifies that wildcards are resolved by
            expanding the pattern to the pre- and postfixes of the words in the word
            lexicon (if there is one), and turning the query into a series of character
            queries, even if it takes a long time to evaluate. An option with a value of
            lexicon-expand=off specifies that wildcards are only resolved by looking up
            character patterns in the search pattern index, not in the lexicon. An
            option with a value of lexicon-expand=heuristic , which is the default,
            specifies that wildcards are resolved by using a series of internal rules,
            such as estimating the number of lexicon entries that need to be scanned,
            seeing if the estimate crosses certain thresholds, and (if appropriate),
            using another way besides lexicon expansion to resolve the query.
            "lexicon-expansion-limit= number " Specifies the limit for lexicon
            expansion. This puts a restriction on the number of lexicon expansions that
            can be performed. If the limit is exceeded, the server may raise an error
            depending on whether the "limit-check" option is set. The default value for
            this option will be 4096. "limit-check" Specifies that an error will be
            raised if the lexicon expansion exceeds the specified limit.
            "no-limit-check" Specifies that error will not be raised if the lexicon
            expansion exceeds the specified limit. The server will try to resolve the
            wildcard.
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            field_name=_as_expr(field_name),
            text=_as_expr(text),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the field and its words; options are retained as supplied.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [
                _texts_member("field", "field", self.field_name),
                _texts_member("text", "text", self.text),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class GeospatialRegionQuery(CtsQuery):
    """Compile and serialize native ``cts:geospatial-region-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:geospatial-region-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    geospatial_region_reference: XqyExpression
    operation: XqyExpression
    regions: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        geospatial_region_reference: XqyExpression | list[XqyExpression] | None,
        operation: str | XqyExpression,
        regions: XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        geospatial_region_reference : XqyExpression | list[XqyExpression] | None
            Zero or more geospatial path region index references that identify regions
            in your content. To create a reference, see
            cts:geospatial-region-path-reference .
        operation : str | XqyExpression
            The match operation to apply between the regions specified in the
            $geospatial-region-reference parameter and the regions in the $regions
            parameter. Allowed values: contains , covered-by , covers , disjoint ,
            intersects , overlaps , within , equals , touches , crosses . See the Usage
            Notes for details.
        regions : XqyExpression | list[XqyExpression] | None
            Criteria regions to match against the regions specified in the
            $geospatial-region-reference parameter. These regions function as the right
            operand of $operation .
        options : StringInput, optional
            Options to this query. The default is (). Available options: "units= value "
            Measure distances and the radii of circles using the given units. Allowed
            values: miles (default), km , feet , and meters . This option only affects
            regions provided in the $regions parameter, not regions stored in documents.
            "score-function= function " Use the selected scoring function. The score
            function may be: linear Use a linear function of the difference between the
            specified query value and the matching value in the index to calculate a
            score for this range query. reciprocal Use a reciprocal function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. zero This range query does
            not contribute to the score. This is the default. "slope-factor= number "
            Apply the given number as a scaling factor to the slope of the scoring
            function. The default is 1.0. "synonym" Specifies that all of the terms in
            the $regions parameter are considered synonyms for scoring purposes. The
            result is that occurrences of more than one of the synonyms are scored as if
            there are more occurrence of the same term (as opposed to having a separate
            term that contributes to score). "tolerance= distance " Tolerance is the
            largest allowable variation in geometry calculations. If the distance
            between two points is less than tolerance, then the two points are
            considered equal. For the raw coordinate system, use the units of the
            coordinates. For geographic coordinate systems, use the units specified by
            the units option.
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            geospatial_region_reference=_as_expr(geospatial_region_reference),
            operation=_as_expr(operation),
            regions=_as_expr(regions),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _references_member(
                    "geospatialRegionPathReference",
                    self.geospatial_region_reference,
                ),
                _text_member("operation", "operation", self.operation),
                _regions_member("region", "region", self.regions),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class JsonPropertyChildGeospatialQuery(CtsQuery):
    """Compile and serialize this native query.

    Native constructor: ``cts:json-property-child-geospatial-query``.
    """

    _FUNCTION: ClassVar[str] = "cts:json-property-child-geospatial-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    parent_property_name: XqyExpression
    child_property_names: XqyExpression
    regions: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        parent_property_name: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        child_property_names: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        regions: XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        parent_property_name : StringInput
            One or more parent property names to match. When multiple names are
            specified, the query matches if any name matches.
        child_property_names : StringInput
            One or more child property names to match. When multiple names are
            specified, the query matches if any name matches; however, only the first
            matching latitude child in any point instance will be checked. The property
            must specify both latitude and longitude coordinates.
        regions : XqyExpression | list[XqyExpression] | None
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= string " Use the coordinate system at the
            given precision. Allowed values: float (default) and double . "units= value
            " Measure distance and the radii of circles in the specified units. Allowed
            values: miles (default), km , feet , meters . "boundaries-included" Points
            on boxes', circles', and polygons' boundaries are counted as matching. This
            is the default. "boundaries-excluded" Points on boxes', circles', and
            polygons' boundaries are not counted as matching.
            "boundaries-latitude-excluded" Points on boxes' latitude boundaries are not
            counted as matching. "boundaries-longitude-excluded" Points on boxes'
            longitude boundaries are not counted as matching.
            "boundaries-south-excluded" Points on the boxes' southern boundaries are not
            counted as matching. "boundaries-west-excluded" Points on the boxes' western
            boundaries are not counted as matching. "boundaries-north-excluded" Points
            on the boxes' northern boundaries are not counted as matching.
            "boundaries-east-excluded" Points on the boxes' eastern boundaries are not
            counted as matching. "boundaries-circle-excluded" Points on circles'
            boundary are not counted as matching. "boundaries-endpoints-excluded" Points
            on linestrings' boundary (the endpoints) are not counted as matching.
            "cached" Cache the results of this query in the list cache. "uncached" Do
            not cache the results of this query in the list cache. "type=long-lat-point"
            Specifies the format for the point in the data as longitude first, latitude
            second. "type=point" Specifies the format for the point in the data as
            latitude first, longitude second. This is the default format.
            "score-function= function " Use the selected scoring function. The score
            function may be: linear Use a linear function of the difference between the
            specified query value and the matching value in the index to calculate a
            score for this range query. reciprocal Use a reciprocal function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. zero This range query does
            not contribute to the score. This is the default. "slope-factor= number "
            Apply the given number as a scaling factor to the slope of the scoring
            function. The default is 1.0. "synonym" Specifies that all of the terms in
            the $regions parameter are considered synonyms for scoring purposes. The
            result is that occurrences of more than one of the synonyms are scored as if
            there are more occurrence of the same term (as opposed to having a separate
            term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            parent_property_name=_as_expr(parent_property_name),
            child_property_names=_as_expr(child_property_names),
            regions=_as_expr(regions),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member("property", "property", self.parent_property_name),
                _texts_member("child", "child", self.child_property_names),
                _regions_member("region", "region", self.regions),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class JsonPropertyGeospatialQuery(CtsQuery):
    """Compile and serialize native ``cts:json-property-geospatial-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:json-property-geospatial-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    property_name: XqyExpression
    regions: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        property_name: StringInput,
        regions: XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        property_name : StringInput
            One or more json property names to match. When multiple names are specified,
            the query matches if any name matches.
        regions : XqyExpression | list[XqyExpression] | None
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= string " Use the coordinate system at the
            given precision. Allowed values: float (default) and double . "units= value
            " Measure distance and the radii of circles in the specified units. Allowed
            values: miles (default), km , feet , meters . "boundaries-included" Points
            on boxes', circles', and polygons' boundaries are counted as matching. This
            is the default. "boundaries-excluded" Points on boxes', circles', and
            polygons' boundaries are not counted as matching.
            "boundaries-latitude-excluded" Points on boxes' latitude boundaries are not
            counted as matching. "boundaries-longitude-excluded" Points on boxes'
            longitude boundaries are not counted as matching.
            "boundaries-south-excluded" Points on the boxes' southern boundaries are not
            counted as matching. "boundaries-west-excluded" Points on the boxes' western
            boundaries are not counted as matching. "boundaries-north-excluded" Points
            on the boxes' northern boundaries are not counted as matching.
            "boundaries-east-excluded" Points on the boxes' eastern boundaries are not
            counted as matching. "boundaries-circle-excluded" Points on circles'
            boundary are not counted as matching. "boundaries-endpoints-excluded" Points
            on linestrings' boundary (the endpoints) are not counted as matching.
            "cached" Cache the results of this query in the list cache. "uncached" Do
            not cache the results of this query in the list cache. "type=long-lat-point"
            Specifies the format for the point in the data as longitude first, latitude
            second. "type=point" Specifies the format for the point in the data as
            latitude first, longitude second. This is the default format.
            "score-function= function " Use the selected scoring function. The score
            function may be: linear Use a linear function of the difference between the
            specified query value and the matching value in the index to calculate a
            score for this range query. reciprocal Use a reciprocal function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. zero This range query does
            not contribute to the score. This is the default. "slope-factor= number "
            Apply the given number as a scaling factor to the slope of the scoring
            function. The default is 1.0. "synonym" Specifies that all of the terms in
            the $regions parameter are considered synonyms for scoring purposes. The
            result is that occurrences of more than one of the synonyms are scored as if
            there are more occurrence of the same term (as opposed to having a separate
            term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            property_name=_as_expr(property_name),
            regions=_as_expr(regions),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member("property", "property", self.property_name),
                _regions_member("region", "region", self.regions),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class JsonPropertyPairGeospatialQuery(CtsQuery):
    """Compile and serialize this native query.

    Native constructor: ``cts:json-property-pair-geospatial-query``.
    """

    _FUNCTION: ClassVar[str] = "cts:json-property-pair-geospatial-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 4

    property_name: XqyExpression
    latitude_property_names: XqyExpression
    longitude_property_names: XqyExpression
    regions: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        property_name: StringInput,
        latitude_property_names: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        longitude_property_names: str
        | list[str]
        | XqyExpression
        | list[XqyExpression]
        | None,
        regions: XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        property_name : StringInput
            One or more parent property names to match. When multiple names are
            specified, the query matches if any name matches.
        latitude_property_names : StringInput
            One or more latitude property names to match. When multiple names are
            specified, the query matches if any name matches; however, only the first
            matching latitude child in any point instance will be checked.
        longitude_property_names : StringInput
            One or more longitude property names to match. When multiple names are
            specified, the query matches if any name matches; however, only the first
            matching longitude child in any point instance will be checked.
        regions : XqyExpression | list[XqyExpression] | None
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            property_name=_as_expr(property_name),
            latitude_property_names=_as_expr(latitude_property_names),
            longitude_property_names=_as_expr(longitude_property_names),
            regions=_as_expr(regions),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member("property", "property", self.property_name),
                _texts_member("latitude", "latitude", self.latitude_property_names),
                _texts_member("longitude", "longitude", self.longitude_property_names),
                _regions_member("region", "region", self.regions),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class JsonPropertyRangeQuery(CtsQuery):
    """Compile and serialize native ``cts:json-property-range-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:json-property-range-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    property_name: XqyExpression
    operator: XqyExpression
    value: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        property_name: StringInput,
        operator: str | XqyExpression,
        value: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        property_name : StringInput
            One or more property name to match. When multiple names are specified, the
            query matches if any name matches.
        operator : str | XqyExpression
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : AtomicInput
            One or more property values to match. When multiple values are specified,
            the query matches if any value matches. The value must be a type for which
            there is a range index defined.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            property_name=_as_expr(property_name),
            operator=_operator_argument(operator),
            value=_as_expr(value),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member("property", "property", self.property_name),
                _attribute_member("operator", "operator", self.operator),
                _typed_member("value", "value", self.value),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class JsonPropertyScopeQuery(CtsQuery):
    """Compile and serialize native ``cts:json-property-scope-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:json-property-scope-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    property_name: XqyExpression
    query: XqyExpression

    def __init__(self, property_name: StringInput, query: StringInput):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        property_name : StringInput
            One or more property names to match. When multiple names are specified, the
            query matches if any name matches.
        query : str | XqyExpression
            A query for the property to match. If a string is entered, the string is
            treated as a cts:word-query of the specified string.
        """
        self._snapshot(
            property_name=_as_expr(property_name),
            query=_as_expr(query),
        )

    def _serialize(self, output_format):
        """Serialize the scoping properties and the nested query.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [
                _texts_member("property", "property", self.property_name),
                _query_member("query", "query", self.query),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class JsonPropertyValueQuery(CtsQuery):
    """Compile and serialize native ``cts:json-property-value-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:json-property-value-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    property_name: XqyExpression
    value: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        property_name: StringInput,
        value: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        property_name : StringInput
            One or more property names to match. When multiple names are specified, the
            query matches if any name matches.
        value : AtomicInput
            One or more property values to match. When multiple values are specified,
            the query matches if any value matches. The values can be strings, numbers
            or booleans to match correspondingly typed nodes. If the value is the empty
            sequence, the query matches null.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "min-occurs= number " Specifies the minimum number of
            occurrences required. If fewer that this number of words occur, the fragment
            does not match. The default is 1. "max-occurs= number " Specifies the
            maximum number of occurrences required. If more than this number of words
            occur, the fragment does not match. The default is unbounded. "synonym"
            Specifies that all of the terms in the $text parameter are considered
            synonyms for scoring purposes. The result is that occurrences of more than
            one of the synonyms are scored as if there are more occurrences of the same
            term (as opposed to having a separate term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            property_name=_as_expr(property_name),
            value=_as_expr(value),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member("property", "property", self.property_name),
                _json_values_member("value", "value", self.value),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class JsonPropertyWordQuery(CtsQuery):
    """Compile and serialize native ``cts:json-property-word-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:json-property-word-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    property_name: XqyExpression
    text: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        property_name: StringInput,
        text: StringInput,
        *,
        options=None,
        weight=None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        property_name : StringInput
            One or more JSON property names to match. When multiple names are specified,
            the query matches if any name matches.
        text : StringInput
            Some words or phrases to match. When multiple strings are specified, the
            query matches if any string matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "case-sensitive"
            A case-sensitive query. "case-insensitive" A case-insensitive query.
            "diacritic-sensitive" A diacritic-sensitive query. "diacritic-insensitive" A
            diacritic-insensitive query. "punctuation-sensitive" A punctuation-sensitive
            query. "punctuation-insensitive" A punctuation-insensitive query.
            "whitespace-sensitive" A whitespace-sensitive query.
            "whitespace-insensitive" A whitespace-insensitive query. "stemmed" A stemmed
            query. "unstemmed" An unstemmed query. "wildcarded" A wildcarded query.
            "unwildcarded" An unwildcarded query. "exact" An exact match query.
            Shorthand for "case-sensitive", "diacritic-sensitive",
            "punctuation-sensitive", "whitespace-sensitive", "unstemmed", and
            "unwildcarded". "lang= iso639code " Specifies the language of the query. The
            iso639code code portion is case-insensitive, and uses the languages
            specified by ISO 639 . The default is specified in the database
            configuration. "distance-weight= number " A weight applied based on the
            minimum distance between matches of this query. Higher weights add to the
            importance of proximity (as opposed to term matches) when the relevance
            order is calculated. The default value is 0.0 (no impact of proximity). The
            weight should be between 64 and -16. Weights greater than 64 will have the
            same effect as a weight of 64. This parameter has no effect if the word
            positions index is not enabled. This parameter has no effect on searches
            that use score-simple, score-random, or score-zero (because those scoring
            algorithms do not consider term frequency, proximity is irrelevant).
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "synonym" Specifies that all of
            the terms in the $text parameter are considered synonyms for scoring
            purposes. The result is that occurrences of more than one of the synonyms
            are scored as if there are more occurrences of the same term (as opposed to
            having a separate term that contributes to score). "lexicon-expand= value "
            The value is one of full , prefix-postfix , off , or heuristic (the default
            is heuristic ). An option with a value of lexicon-expand=full specifies that
            wildcards are resolved by expanding the pattern to words in a lexicon (if
            there is one available), and turning into a series of cts:word-queries ,
            even if this takes a long time to evaluate. An option with a value of
            lexicon-expand=prefix-postfix specifies that wildcards are resolved by
            expanding the pattern to the pre- and postfixes of the words in the word
            lexicon (if there is one), and turning the query into a series of character
            queries, even if it takes a long time to evaluate. An option with a value of
            lexicon-expand=off specifies that wildcards are only resolved by looking up
            character patterns in the search pattern index, not in the lexicon. An
            option with a value of lexicon-expand=heuristic , which is the default,
            specifies that wildcards are resolved by using a series of internal rules,
            such as estimating the number of lexicon entries that need to be scanned,
            seeing if the estimate crosses certain thresholds, and (if appropriate),
            using another way besides lexicon expansion to resolve the query.
            "lexicon-expansion-limit= number " Specifies the limit for lexicon
            expansion. This puts a restriction on the number of lexicon expansions that
            can be performed. If the limit is exceeded, the server may raise an error
            depending on whether the "limit-check" option is set. The default value for
            this option will be 4096. "limit-check" Specifies that an error will be
            raised if the lexicon expansion exceeds the specified limit.
            "no-limit-check" Specifies that error will not be raised if the lexicon
            expansion exceeds the specified limit. The server will try to resolve the
            wildcard. "no-limit-check" is default, if neither "limit-check" nor
            "no-limit-check" is explicitly specified.
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            property_name=_as_expr(property_name),
            text=_as_expr(text),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the properties and their words; options are retained as supplied.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [
                _texts_member("property", "property", self.property_name),
                _texts_member("text", "text", self.text),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class LocksFragmentQuery(CtsQuery):
    """Compile and serialize native ``cts:locks-fragment-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:locks-fragment-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    query: XqyExpression

    def __init__(self, query: StringInput):
        """Snapshot constructor arguments.

        Parameters
        ----------
        query : str | XqyExpression
            A query to be matched against the locks fragment.
        """
        self._snapshot(
            query=_as_expr(query),
        )

    def _serialize(self, output_format):
        """Serialize the nested query.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [_query_member("query", "query", self.query)],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class LsqtQuery(CtsQuery):
    """Compile and serialize native ``cts:lsqt-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:lsqt-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    temporal_collection: XqyExpression
    timestamp: XqyExpression | None
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        temporal_collection: str | XqyExpression,
        *,
        timestamp: datetime.datetime | XqyExpression | None = None,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        temporal_collection : str | XqyExpression
            The name of the temporal collection.
        timestamp : datetime.datetime | XqyExpression | None, optional
            Return only temporal documents with a system start time less than or equal
            to this value. Default is temporal:get-lsqt($temporal-collection) .
            Timestamps larger than LSQT are rejected.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "cached-incremental" Break down the
            query into sub-queries and then cache each one of them for better
            performance. This is enabled, by default. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            temporal_collection=_as_expr(temporal_collection),
            timestamp=_optional(timestamp),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _text_member(
                    "temporalCollection",
                    "temporal-collection",
                    self.temporal_collection,
                ),
                _lexical_member("timestamp", "timestamp", self.timestamp),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class NearQuery(CtsQuery):
    """Match subqueries within a native word-distance constraint."""

    _FUNCTION: ClassVar[str] = "cts:near-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    queries: XqyExpression
    distance: XqyExpression | None
    options: XqyExpression | None
    distance_weight: XqyExpression | None

    def __init__(
        self,
        queries: StringInput,
        *,
        distance=None,
        options=None,
        distance_weight=None,
    ):
        """Snapshot proximity arguments.

        Parameters
        ----------
        queries : StringInput
            Child queries, including implicitly converted words.
        distance : float or XqyExpression or None, default None
            Maximum distance, with native default 10.
        options : StringInput, default None
            Ordering and minimum-distance options.
        distance_weight : float or XqyExpression or None, default None
            Weight of proximity in scoring.
        """
        self._snapshot(
            queries=_as_expr(queries),
            distance=_optional_double(distance),
            options=_near_options_argument(options),
            distance_weight=_optional_double(distance_weight),
        )

    def _serialize(self, output_format):
        """Serialize the queries with the distance MarkLogic reads back natively.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        ValueError
            For unsupported or inconsistent ordering and minimum-distance options.
        """
        options, minimum = _near_options(_strings(self.options))
        distance = 10 if self.distance is None else _near_distance(self.distance)
        return self._native(
            [
                _weight_member("weight", "weight", self.distance_weight),
                _QueriesMember("queries", "", _sequence(self.queries)),
                _AttributeMember("distance", "distance", distance),
                _AttributeMember(
                    "minimum-distance",
                    "minimum-distance",
                    minimum or None,
                ),
                _TextsMember("options", "option", options),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class NotInQuery(CtsQuery):
    """Compile and serialize native ``cts:not-in-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:not-in-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    positive_query: XqyExpression
    negative_query: XqyExpression

    def __init__(self, positive_query: StringInput, negative_query: StringInput):
        """Snapshot constructor arguments.

        Parameters
        ----------
        positive_query : str | XqyExpression
            A positive query, specifying the search results filtered in.
        negative_query : str | XqyExpression
            A negative query, specifying the search results to filter out.
        """
        self._snapshot(
            positive_query=_as_expr(positive_query),
            negative_query=_as_expr(negative_query),
        )

    def _serialize(self, output_format):
        """Serialize the positive and negative queries in native wrappers.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [
                _WrappedQueryMember("positiveQuery", "positive", self.positive_query),
                _WrappedQueryMember("negativeQuery", "negative", self.negative_query),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class NotQuery(CtsQuery):
    """Compile and serialize native ``cts:not-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:not-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    query: XqyExpression

    def __init__(self, query: StringInput):
        """Snapshot constructor arguments.

        Parameters
        ----------
        query : str | XqyExpression
            A negative query, specifying the search results to filter out.
        """
        self._snapshot(
            query=_as_expr(query),
        )

    def _serialize(self, output_format):
        """Serialize the negated query.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [_query_member("query", "query", self.query)],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class OrQuery(CtsQuery):
    """Union subqueries using the native CTS constructor."""

    _FUNCTION: ClassVar[str] = "cts:or-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    queries: XqyExpression
    options: XqyExpression | None

    def __init__(self, queries: StringInput, *, options: StringInput = None):
        """Snapshot the subqueries and optional ordering flags.

        Parameters
        ----------
        queries : StringInput
            Subqueries or strings implicitly converted by MarkLogic to word queries.
        options : StringInput, default None
            Native or-query options.
        """
        self._snapshot(
            queries=_as_expr(queries),
            options=_choice_options_argument(options, _OR_OPTIONS, "or-query"),
        )

    def _serialize(self, output_format):
        """Serialize the union with native child-query cardinality.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        ValueError
            For options other than synonym.
        """
        options = _strings(self.options)
        _check_choice_options(options, _OR_OPTIONS, "or-query")
        return self._native(
            [
                _QueriesMember("queries", "", _sequence(self.queries)),
                _TextsMember("options", "option", options),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class PathGeospatialQuery(CtsQuery):
    """Compile and serialize native ``cts:path-geospatial-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:path-geospatial-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    path_expression: XqyExpression
    regions: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        path_expression: StringInput,
        regions: XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        path_expression : StringInput
            One or more path expressions to match. When multiple path expressions are
            specified, the query matches if any path expression matches.
        regions : XqyExpression | list[XqyExpression] | None
            One or more geographic boxes, circles, polygons, or points. Where multiple
            regions are specified, the query matches if any region matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include:
            "coordinate-system= string " Use the given coordinate system. Valid values
            are: wgs84 The WGS84 coordinate system with degrees as the angular unit.
            wgs84/radians The WGS84 coordinate system with radians as the angular unit.
            wgs84/double The WGS84 coordinate system at double precision with degrees as
            the angular unit. wgs84/radians/double The WGS84 coordinate system at double
            precision with radians as the angular unit. etrs89 The ETRS89 coordinate
            system. etrs89/double The ETRS89 coordinate system at double precision. raw
            The raw (unmapped) coordinate system. raw/double The raw coordinate system
            at double precision. "precision= value " Use the coordinate system at the
            given precision. Allowed values: float and double . "units= value " Measure
            distance and the radii of circles in the specified units. Allowed values:
            miles (default), km , feet , meters . "boundaries-included" Points on
            boxes', circles', and polygons' boundaries are counted as matching. This is
            the default. "boundaries-excluded" Points on boxes', circles', and polygons'
            boundaries are not counted as matching. "boundaries-latitude-excluded"
            Points on boxes' latitude boundaries are not counted as matching.
            "boundaries-longitude-excluded" Points on boxes' longitude boundaries are
            not counted as matching. "boundaries-south-excluded" Points on the boxes'
            southern boundaries are not counted as matching. "boundaries-west-excluded"
            Points on the boxes' western boundaries are not counted as matching.
            "boundaries-north-excluded" Points on the boxes' northern boundaries are not
            counted as matching. "boundaries-east-excluded" Points on the boxes' eastern
            boundaries are not counted as matching. "boundaries-circle-excluded" Points
            on circles' boundary are not counted as matching.
            "boundaries-endpoints-excluded" Points on linestrings' boundary (the
            endpoints) are not counted as matching. "cached" Cache the results of this
            query in the list cache. "uncached" Do not cache the results of this query
            in the list cache. "type=long-lat-point" Specifies the format for the point
            in the data as longitude first, latitude second. "type=point" Specifies the
            format for the point in the data as latitude first, longitude second. This
            is the default format. "score-function= function " Use the selected scoring
            function. The score function may be: linear Use a linear function of the
            difference between the specified query value and the matching value in the
            index to calculate a score for this range query. reciprocal Use a reciprocal
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query. zero
            This range query does not contribute to the score. This is the default.
            "slope-factor= number " Apply the given number as a scaling factor to the
            slope of the scoring function. The default is 1.0. "synonym" Specifies that
            all of the terms in the $regions parameter are considered synonyms for
            scoring purposes. The result is that occurrences of more than one of the
            synonyms are scored as if there are more occurrence of the same term (as
            opposed to having a separate term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            path_expression=_as_expr(path_expression),
            regions=_as_expr(regions),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member(
                    "pathExpression",
                    "path-expression",
                    self.path_expression,
                ),
                _regions_member("region", "region", self.regions),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class PathRangeQuery(CtsQuery):
    """Compile and serialize native ``cts:path-range-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:path-range-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    path_expression: XqyExpression
    operator: XqyExpression
    value: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        path_expression: StringInput,
        operator: str | XqyExpression,
        value: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        path_expression : StringInput
            One or more XPath expressions that identify the content to match. When
            multiple paths are specified, the query matches if any path matches.
        operator : str | XqyExpression
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : AtomicInput
            One or more values to match. These values are compared to the value(s)
            addressed by the path-expression parameter. When multiple When multiple
            values are specified, the query matches if any value matches. The value must
            be a type for which there is a range index defined.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "collation= URI "
            Use the range index with the collation specified by URI . If not specified,
            then the default collation from the query is used. If a range index with the
            specified collation does not exist, an error is thrown. "cached" Cache the
            results of this query in the list cache. "uncached" Do not cache the results
            of this query in the list cache. "cached-incremental" When querying on a
            short date or dateTime range, break the query into sub-queries on smaller
            ranges, and then cache the results of each. See the Usage Notes for details.
            "min-occurs= number " Specifies the minimum number of occurrences required.
            If fewer that this number of words occur, the fragment does not match. The
            default is 1. "max-occurs= number " Specifies the maximum number of
            occurrences required. If more than this number of words occur, the fragment
            does not match. The default is unbounded. "score-function= function " Use
            the selected scoring function. The score function may be: linear Use a
            linear function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
            "synonym" Specifies that all of the terms in the $value parameter are
            considered synonyms for scoring purposes. The result is that occurrences of
            more than one of the synonyms are scored as if there are more occurrences of
            the same term (as opposed to having a separate term that contributes to
            score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            path_expression=_as_expr(path_expression),
            operator=_operator_argument(operator),
            value=_as_expr(value),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member(
                    "pathExpression",
                    "path-expression",
                    self.path_expression,
                ),
                _attribute_member("operator", "operator", self.operator),
                _typed_member("value", "value", self.value),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class PeriodCompareQuery(CtsQuery):
    """Compile and serialize native ``cts:period-compare-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:period-compare-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    axis_1: XqyExpression
    operator: XqyExpression
    axis_2: XqyExpression
    options: XqyExpression | None

    def __init__(
        self,
        axis_1: str | XqyExpression,
        operator: str | XqyExpression,
        axis_2: str | XqyExpression,
        *,
        options: StringInput = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        axis_1 : str | XqyExpression
            Name of the first axis to compare
        operator : str | XqyExpression
            A comparison operator. Period is the two timestamps contained in the axis.
            Operators include: "aln_equals" Match documents whose period1 equals
            period2. "aln_contains" Match documents whose period1 contains period2. i.e.
            period1 starts before period2 starts and ends before period2 ends.
            "aln_contained_by" Match documents whose period1 is contained by period2.
            "aln_meets" Match documents whose period1 meets period2, i.e. period1 ends
            at period2 start. "aln_met_by" Match documents whose period1 meets period2,
            i.e. period1 starts at period2 end. "aln_before" Match documents whose
            period1 is before period2, i.e. period1 ends before period2 starts.
            "aln_after" Match documents whose period1 is after period2, i.e. period1
            starts after period2 ends. "aln_starts" Match documents whose period1 starts
            period2, i.e. period1 starts at period2 start and ends before period2 ends.
            "aln_started_by" Match documents whose period2 starts period1, i.e. period1
            starts at period2 start and ends after period2 ends. "aln_finishes" Match
            documents whose period1 finishes period2, i.e. period1 finishes at period2
            finish and starts after period2 starts. "aln_finished_by" Match documents
            whose period2 finishes period1, i.e. period1 finishes at period2 finish and
            starts before period2 starts. "aln_overlaps" Match documents whose period1
            overlaps period2, i.e. period1 starts before period2 start and ends before
            period2 ends but after period2 starts. "aln_overlapped_by" Match documents
            whose period2 overlaps period1, i.e. period1 starts after period2 start but
            before period2 ends and ends after period2 ends. "iso_contains" Match
            documents whose period1 contains period2 in sql 2011 standard. i.e. period1
            starts before or at period2 starts and ends after or at period2 ends.
            "iso_overlaps" Match documents whose period1 overlaps period2 in sql 2011
            standard. i.e. period1 and period2 have common time period. "iso_succeeds"
            Match documents whose period1 succeeds period2 in sql 2011 standard. i.e.
            period1 starts at or after period2 ends "iso_precedes" Match documents whose
            period1 precedes period2 in sql 2011 standard. i.e. period1 ends at or
            before period2 ends "iso_succeeds" Match documents whose period1 succeeds
            period2 in sql 2011 standard. i.e. period1 starts at or after period2 ends
            "iso_precedes" Match documents whose period1 precedes period2 in sql 2011
            standard. i.e. period1 ends at or before period2 ends "iso_imm_succeeds"
            Match documents whose period1 immediately succeeds period2 in sql 2011
            standard. i.e. period1 starts at period2 ends "iso_imm_precedes" Match
            documents whose period1 immediately precedes period2 in sql 2011 standard.
            i.e. period1 ends at period2 ends
        axis_2 : str | XqyExpression
            Name of the second period to compare
        options : StringInput, optional
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache.
        """
        self._snapshot(
            axis_1=_as_expr(axis_1),
            operator=_temporal_operator_argument(operator),
            axis_2=_as_expr(axis_2),
            options=_optional(options),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _text_member("axis1", "axis1", self.axis_1),
                _attribute_member("operator", "operator", self.operator),
                _text_member("axis2", "axis2", self.axis_2),
                _texts_member("options", "option", self.options),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class PeriodRangeQuery(CtsQuery):
    """Compile and serialize native ``cts:period-range-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:period-range-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 2

    axis_name: XqyExpression
    operator: XqyExpression
    period: XqyExpression | None
    options: XqyExpression | None

    def __init__(
        self,
        axis_name: StringInput,
        operator: str | XqyExpression,
        *,
        period: XqyExpression | list[XqyExpression] | None = None,
        options: StringInput = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        axis_name : StringInput
            One or more axis to match on.
        operator : str | XqyExpression
            A comparison operator. Operators include: "aln_equals" Match documents whose
            period1 equals value. "aln_contains" Match documents whose period1 contains
            value. i.e. period1 starts before value starts and ends before value ends.
            "aln_contained_by" Match documents whose period1 is contained by value.
            "aln_meets" Match documents whose period1 meets value, i.e. period1 ends at
            value start. "aln_met_by" Match documents whose period1 meets value, i.e.
            period1 starts at value end. "aln_before" Match documents whose period1 is
            before value, i.e. period1 ends before value starts. "aln_after" Match
            documents whose period1 is after value, i.e. period1 starts after value
            ends. "aln_starts" Match documents whose period1 starts value, i.e. period1
            starts at value start and ends before value ends. "aln_started_by" Match
            documents whose value starts period1, i.e. period1 starts at value start and
            ends after value ends. "aln_finishes" Match documents whose period1 finishes
            value, i.e. period1 finishes at value finish and starts after value starts.
            "aln_finished_by" Match documents whose value finishes period1, i.e. period1
            finishes at value finish and starts before value starts. "aln_overlaps"
            Match documents whose period1 overlaps value, i.e. period1 starts before
            value start and ends before value ends but after value starts.
            "aln_overlapped_by" Match documents whose value overlaps period1, i.e.
            period1 starts after value start but before value ends and ends after value
            ends. "iso_contains" Match documents whose period1 contains value in sql
            2011 standard. i.e. period1 starts before or at value starts and ends after
            or at value ends. "iso_overlaps" Match documents whose period1 overlaps
            value in sql 2011 standard. i.e. period1 and value have common time period.
            "iso_succeeds" Match documents whose period1 succeeds value in sql 2011
            standard. i.e. period1 starts at or after value ends "iso_precedes" Match
            documents whose period1 precedes value in sql 2011 standard. i.e. period1
            ends at or before value ends "iso_imm_succeeds" Match documents whose
            period1 immediately succeeds value in sql 2011 standard. i.e. period1 starts
            at value end "iso_imm_precedes" Match documents whose period1 immediately
            precedes value in sql 2011 standard. i.e. period1 ends at value end
        period : XqyExpression | list[XqyExpression] | None, optional
            the cts:period to perform operations on. When multiple values are specified,
            the query matches if any value matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "min-occurs= number " Specifies the
            minimum number of occurrences required. If fewer that this number of words
            occur, the fragment does not match. The default is 1. "max-occurs= number "
            Specifies the maximum number of occurrences required. If more than this
            number of words occur, the fragment does not match. The default is
            unbounded. "score-function= function " Use the selected scoring function.
            The score function may be: linear Use a linear function of the difference
            between the specified query value and the matching value in the index to
            calculate a score for this range query. reciprocal Use a reciprocal function
            of the difference between the specified query value and the matching value
            in the index to calculate a score for this range query. zero This range
            query does not contribute to the score. This is the default. "slope-factor=
            number " Apply the given number as a scaling factor to the slope of the
            scoring function. The default is 1.0.
        """
        self._snapshot(
            axis_name=_as_expr(axis_name),
            operator=_temporal_operator_argument(operator),
            period=_optional(period),
            options=_optional(options),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _texts_member("axis", "axis", self.axis_name),
                _attribute_member("operator", "operator", self.operator),
                _periods_member("period", "period", self.period),
                _texts_member("options", "option", self.options),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class PropertiesFragmentQuery(CtsQuery):
    """Compile and serialize native ``cts:properties-fragment-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:properties-fragment-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    query: XqyExpression

    def __init__(self, query: StringInput):
        """Snapshot constructor arguments.

        Parameters
        ----------
        query : str | XqyExpression
            A query to be matched against the properties fragment.
        """
        self._snapshot(
            query=_as_expr(query),
        )

    def _serialize(self, output_format):
        """Serialize the nested query.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [_query_member("query", "query", self.query)],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class RangeQuery(CtsQuery):
    """Compile and serialize native ``cts:range-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:range-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    index: XqyExpression
    operator: XqyExpression
    value: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        index: XqyExpression | list[XqyExpression] | None,
        operator: str | XqyExpression,
        value: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        index : XqyExpression | list[XqyExpression] | None
            One or more range index references. When multiple indexes are specified, the
            query matches if any index matches.
        operator : str | XqyExpression
            A comparison operator. Operators include: "<" Match range index values less
            than $value. "<=" Match range index values less than or equal to $value. ">"
            Match range index values greater than $value. ">=" Match range index values
            greater than or equal to $value. "=" Match range index values equal to
            $value. "!=" Match range index values not equal to $value.
        value : AtomicInput
            One or more values to match. When multiple values are specified, the query
            matches if any value matches.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "min-occurs= number " Specifies the
            minimum number of occurrences required. If fewer that this number of words
            occur, the fragment does not match. The default is 1. "max-occurs= number "
            Specifies the maximum number of occurrences required. If more than this
            number of words occur, the fragment does not match. The default is
            unbounded. "score-function= function " Use the selected scoring function.
            The score function may be: linear Use a linear function of the difference
            between the specified query value and the matching value in the index to
            calculate a score for this range query. reciprocal Use a reciprocal function
            of the difference between the specified query value and the matching value
            in the index to calculate a score for this range query. zero This range
            query does not contribute to the score. This is the default. "slope-factor=
            number " Apply the given number as a scaling factor to the slope of the
            scoring function. The default is 1.0. "synonym" Specifies that all of the
            terms in the $value parameter are considered synonyms for scoring purposes.
            The result is that occurrences of more than one of the synonyms are scored
            as if there are more occurrences of the same term (as opposed to having a
            separate term that contributes to score).
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            index=_as_expr(index),
            operator=_operator_argument(operator),
            value=_as_expr(value),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _references_member("reference", self.index),
                _attribute_member("operator", "operator", self.operator),
                _typed_member("value", "value", self.value),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class RegisteredQuery(CtsQuery):
    """Compile and serialize native ``cts:registered-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:registered-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    ids: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        ids: int | list[int] | XqyExpression | list[XqyExpression] | None,
        *,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        ids : int | list[int] | XqyExpression | list[XqyExpression] | None
            Some registered query identifiers.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "filtered" A
            filtered query (the default). Filtered queries eliminate any false-positive
            results and properly resolve cases where there are multiple candidate
            matches within the same fragment, thereby guaranteeing that the results
            fully satisfy the original cts:query item that was registered. This option
            is not currently available. "unfiltered" An unfiltered query. Unfiltered
            registered queries select fragments from the indexes that are candidates to
            satisfy the cts:query . Depending on the original cts:query , the structure
            of the documents in the database, and the configuration of the database,
            unfiltered registered queries may result in false-positive results or in
            incorrect matches when there are multiple candidate matches within the same
            fragment. To avoid these problems, you should only use unfiltered queries on
            top-level XPath expressions (for example, document nodes, collections,
            directories) or on fragment roots. Using unfiltered queries on complex XPath
            expressions or on XPath expressions that traverse below a fragment root can
            result in unexpected results. This option is required in the current
            release.
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        """
        self._snapshot(
            ids=_as_expr(ids),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _lexicals_member("ids", "id", self.ids),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class ReverseQuery(CtsQuery):
    """Compile and serialize native ``cts:reverse-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:reverse-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    nodes: XqyExpression
    weight: XqyExpression | None

    def __init__(
        self,
        nodes: NodeInput,
        *,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        nodes : NodeInput
            Model nodes that must be matchable by queries matched by this reverse query.
            See the Usage Notes for more details.
        weight : float | XqyExpression | None, optional
            A weight for this query. This parameter has no effect because a reverse
            query does not contribute to score. That is, the score is always 0.
        """
        self._snapshot(
            nodes=_as_expr(nodes),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _nodes_member("nodes", "node", self.nodes),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class RuntimeQuery(CtsQuery):
    """Compile a CTS query whose native representation requires evaluation."""

    expression: XqyExpression

    def __init__(self, expression: XqyExpression):
        """Retain the expression producing a query.

        Parameters
        ----------
        expression : XqyExpression
            Query-producing expression evaluated by MarkLogic.
        """
        self._snapshot(expression=expression)

    @property
    def _error_label(self) -> str:
        """Name this query in serialization errors.

        Returns
        -------
        str
            ``runtime query``, as no native constructor describes it.
        """
        return "runtime query"

    def render(self, ctx: XqyCompilationContext) -> str:
        """Render the query-producing expression.

        Parameters
        ----------
        ctx : XqyCompilationContext
            Shared compilation context.

        Returns
        -------
        str
            Native call with externally bound arguments.
        """
        return self.expression.render(ctx)

    def _serialize(self, _output_format):
        """Reject local serialization of a runtime-determined query.

        Parameters
        ----------
        _output_format : {'json', 'xml'}
            Requested representation.

        Raises
        ------
        TypeError
            The native query must first be evaluated on MarkLogic.
        """
        message = "CTS runtime query requires server evaluation before serialization."
        raise TypeError(message)


@dataclass(frozen=True, init=False, repr=False)
class SimilarQuery(CtsQuery):
    """Compile and serialize native ``cts:similar-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:similar-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    nodes: XqyExpression
    weight: XqyExpression | None
    options: XqyExpression | None

    def __init__(
        self,
        nodes: NodeInput,
        *,
        weight: float | XqyExpression | None = None,
        options: NodeInput = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        nodes : NodeInput
            Some model nodes.
        weight : float | XqyExpression | None, optional
            A weight for this query. Higher weights move search results up in the
            relevance order. The default is 1.0. The weight should be between 64 and
            -16. Weights greater than 64 will have the same effect as a weight of 64.
            Weights less than the absolute value of 0.0625 (between -0.0625 and 0.0625)
            are rounded to 0, which means that they do not contribute to the score.
        options : NodeInput, optional
            An XML representation of the options for defining which terms to generate
            and how to evaluate them. The options node must be in the
            cts:distinctive-terms namespace. The following is a sample options node :
            <options xmlns="cts:distinctive-terms"> <max-terms>20</max-terms> </options>
            See the cts:distinctive-terms options for the valid options to use with this
            function. Note that enabling index settings that are disabled in the
            database configuration will not affect the results, as similar documents
            will not be found on the basis of terms that do not exist in the actual
            database index.
        """
        self._snapshot(
            nodes=_as_expr(nodes),
            weight=_optional_double(weight),
            options=_optional(options),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                _nodes_member("nodes", "node", self.nodes),
                _weight_member("weight", "weight", self.weight),
                _distinctive_options_member(self.options),
            ],
            output_format,
        )


@dataclass(frozen=True, init=False, repr=False)
class TripleRangeQuery(CtsQuery):
    """Compile and serialize native ``cts:triple-range-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:triple-range-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 3

    subject: XqyExpression
    predicate: XqyExpression
    object: XqyExpression
    operator: XqyExpression | None
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(
        self,
        subject: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        predicate: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        object: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        operator: StringInput = None,
        options: StringInput = None,
        weight: float | XqyExpression | None = None,
    ):
        """Snapshot native constructor arguments.

        Parameters
        ----------
        subject : AtomicInput
            The subjects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any subject are matched.
        predicate : AtomicInput
            The predicates to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any predicate are matched.
        object : AtomicInput
            The objects to look up. When multiple values are specified, the query
            matches if any value matches. When the empty sequence is specified, then
            triples with any object are matched.
        operator : StringInput, optional
            One object operator or three subject/predicate/object operators.
            Includes sameTerm; empty sequences use the native default.
            MarkLogic validates these operators when the query is evaluated.
        options : StringInput, optional
            Options to this query. The default is (). Options include: "cached" Cache
            the results of this query in the list cache. "uncached" Do not cache the
            results of this query in the list cache. "score-function= function " Use the
            selected scoring function. The score function may be: linear Use a linear
            function of the difference between the specified query value and the
            matching value in the index to calculate a score for this range query.
            reciprocal Use a reciprocal function of the difference between the specified
            query value and the matching value in the index to calculate a score for
            this range query. zero This range query does not contribute to the score.
            This is the default. "slope-factor= number " Apply the given number as a
            scaling factor to the slope of the scoring function. The default is 1.0.
        weight : float | XqyExpression | None, optional
            A weight for this query. The default is 1.0.
        """
        self._snapshot(
            subject=_as_expr(subject),
            predicate=_as_expr(predicate),
            object=_as_expr(object),
            operator=_optional(operator),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the native arguments in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.

        Raises
        ------
        TypeError
            For arguments requiring server evaluation.
        ValueError
            For literal values without a local native form.
        """
        return self._native(
            [
                *_triple_operators(self.operator),
                _triples_member("subject", self.subject),
                _triples_member("predicate", self.predicate),
                _triples_member("object", self.object),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


@dataclass(frozen=True, repr=False)
class TrueQuery(CtsQuery):
    """Compile and serialize native ``cts:true-query`` queries."""

    _FUNCTION: ClassVar[str] = "cts:true-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 0

    def _serialize(self, output_format):
        """Serialize the query, which has no arguments.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native([], output_format)


@dataclass(frozen=True, init=False, repr=False)
class WordQuery(CtsQuery):
    """Match words using a compilable and locally serializable CTS query."""

    _FUNCTION: ClassVar[str] = "cts:word-query"
    _REQUIRED_ARGUMENTS: ClassVar[int] = 1

    text: XqyExpression
    options: XqyExpression | None
    weight: XqyExpression | None

    def __init__(self, text: StringInput, *, options=None, weight=None):
        """Snapshot text, options and weight without changing native compilation.

        Parameters
        ----------
        text : StringInput
            Words or phrases, including arbitrary server-evaluated expressions.
        options : StringInput, default None
            Native word-query options.
        weight : float or XqyExpression or None, default None
            Native double weight, omitted when None.
        """
        self._snapshot(
            text=_as_expr(text),
            options=_optional(options),
            weight=_optional_double(weight),
        )

    def _serialize(self, output_format):
        """Serialize the words; options are retained as supplied.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Native query.
        """
        return self._native(
            [
                _texts_member("text", "text", self.text),
                _texts_member("options", "option", self.options),
                _weight_member("weight", "weight", self.weight),
            ],
            output_format,
        )


def _near_options(options):
    """Normalize native near-query ordering and minimum distance.

    Parameters
    ----------
    options : list[str]
        Literal near-query options.

    Returns
    -------
    tuple[list[str], int]
        At most one ordering option and the minimum distance, clamped to the
        native unsigned range; 0 when omitted.

    Raises
    ------
    ValueError
        For other options, a non-integer minimum distance, or repeated
        ordering or minimum-distance options.
    """
    ordering = []
    minimum = []
    for option in options:
        if option in _ORDER_OPTIONS:
            ordering.append(option)
        elif option.startswith("minimum-distance="):
            value = option.removeprefix("minimum-distance=")
            if re.fullmatch(r"[+-]?[0-9]+", value) is None:
                message = f"option {option!r} is not a near-query option"
                raise ValueError(message)
            minimum.append(max(0, min(2**32 - 1, int(value))))
        else:
            message = f"option {option!r} is not a near-query option"
            raise ValueError(message)
    if len(ordering) > 1 or len(minimum) > 1:
        message = f"options {options!r} repeat ordering or minimum-distance"
        raise ValueError(message)
    return ordering, minimum[0] if minimum else 0


def _near_distance(distance):
    """Return the word distance MarkLogic stores for a near-query.

    Parameters
    ----------
    distance : XqyExpression
        The literal distance argument.

    Returns
    -------
    int
        The distance rounded half up, negative values as 0.

    Raises
    ------
    TypeError
        For a distance requiring server evaluation.
    """
    # MarkLogic keeps the distance as an unsigned 32-bit integer, so larger
    # values wrap around: distance=4294967297 round-trips as 1.
    return math.floor(max(0, _number(distance)) + 0.5) % (2**32)


def _subquery(expression, output_format):
    """Serialize one nested query in the format of its parent.

    A literal string stays a word query, as MarkLogic converts it implicitly.

    Parameters
    ----------
    expression : XqyExpression
        A CtsQuery or a literal string.
    output_format : {'json', 'xml'}
        Requested representation.

    Returns
    -------
    dict or xml.etree.ElementTree.Element
        The nested query's native representation.

    Raises
    ------
    TypeError
        For an expression that only the server can evaluate.
    """
    if isinstance(expression, AtomicValue) and expression.cast in (None, "xs:string"):
        expression = WordQuery(expression)
    if not isinstance(expression, CtsQuery):
        message = (
            "CTS subquery requires server evaluation, got "
            f"{_display(expression)}."
        )
        raise TypeError(message)
    return expression.serialize(output_format)


def _json_name(name):
    """Return the native JSON member name of a CTS XML local name.

    Parameters
    ----------
    name : str
        Hyphenated local name, such as and-query.

    Returns
    -------
    str
        Its camel-case JSON name, such as andQuery.
    """
    head, *tail = name.split("-")
    return head + "".join(part.title() for part in tail)


def _text_nodes(root, tag, values):
    """Append one text child per value.

    Parameters
    ----------
    root : xml.etree.ElementTree.Element
        The query element.
    tag : str
        Local name of the children in the cts namespace.
    values : list[str]
        Text of each child, in order.
    """
    for value in values:
        child = SubElement(root, f"{{{CTS_NS_URI}}}{tag}")
        child.text = value


def _weight_text(weight):
    """Format a finite weight using the native double lexical form.

    Parameters
    ----------
    weight : float
        Finite weight.

    Returns
    -------
    str
        Decimal or scientific XML attribute value.
    """
    if weight.is_integer():
        return str(int(weight))
    if abs(weight) >= _SCIENTIFIC_WEIGHT_THRESHOLD:
        return format(Decimal(str(weight)), "f")
    mantissa, exponent = str(weight).split("e")
    if "." not in mantissa:
        mantissa += ".0"
    return f"{mantissa}E{int(exponent)}"


def _sequence(expression):
    """Flatten public sequence values without evaluating expressions.

    Parameters
    ----------
    expression : XqyExpression or None
        Normalized function argument.

    Returns
    -------
    list[XqyExpression]
        Leaf expressions in source order.
    """
    if expression is None:
        return []
    if isinstance(expression, XqySequence):
        return [item for child in expression.items for item in _sequence(child)]
    return [expression]


def _strings(expression):
    """Read literal string arguments through public expression fields.

    Parameters
    ----------
    expression : XqyExpression or None
        Normalized string argument.

    Returns
    -------
    list[str]
        Literal strings.

    Raises
    ------
    TypeError
        When an argument cannot be resolved locally as strings.
    """
    result = []
    for item in _sequence(expression):
        if (
            isinstance(item, FunctionCall)
            and item.fn == "xs:string"
            and len(item.args) == 1
            and not item.optionals
        ):
            result.extend(_strings(item.args[0]))
            continue
        if not isinstance(item, AtomicValue) or item.cast not in (None, "xs:string"):
            message = (
                "CTS string argument requires server evaluation, got "
                f"{_display(item)}."
            )
            raise TypeError(message)
        result.append(item.value)
    return result


def _number(expression):
    """Resolve a literal number, optionally wrapped in an xs:double or xs:float cast.

    Parameters
    ----------
    expression : XqyExpression
        Literal numeric value, such as a weight or a coordinate.

    Returns
    -------
    float
        Literal value.

    Raises
    ------
    TypeError
        For values requiring server evaluation.
    ValueError
        For non-finite literal values.
    """
    if (
        isinstance(expression, FunctionCall)
        and expression.fn in {"xs:double", "xs:float"}
        and len(expression.args) == 1
        and not expression.optionals
    ):
        return _number(expression.args[0])
    if isinstance(expression, AtomicValue) and expression.cast in {
        "xs:integer",
        "xs:double",
        "xs:decimal",
    }:
        value = float(expression.value)
        if not math.isfinite(value):
            message = "CTS numbers must be finite for local serialization."
            raise ValueError(message)
        return value
    message = (
        "CTS numeric argument requires server evaluation, got "
        f"{_display(expression)}."
    )
    raise TypeError(message)


def _render(name, members, output_format):
    """Render described members as one native CTS element.

    Parameters
    ----------
    name : str
        Native XML local name, such as and-query or element-reference.
    members : list[_Member]
        Fields in native XML child order.
    output_format : {'json', 'xml'}
        Requested representation.

    Returns
    -------
    dict or xml.etree.ElementTree.Element
        Fresh native representation; omitted members are left out.
    """
    members = [member for member in members if not member.omitted]
    if output_format == "json":
        fields = {}
        for member in members:
            with _error_context(member.json_key):
                fields[member.json_key] = member.to_json()
        return {_json_name(name): fields}
    root = Element(f"{{{CTS_NS_URI}}}{name}")
    for member in members:
        with _error_context(member.json_key):
            member.add_to_xml(root)
    return root


@dataclass(frozen=True)
class _Member(ABC):
    """One native field of a CTS query, described once for both formats.

    Parameters
    ----------
    json_key : str
        Native JSON member name.
    xml_tag : str
        Native XML child element or attribute local name; unused by members
        whose XML form is a complete element of its own.
    values : object
        Locally resolved values; None or [] omits the field.
    """

    json_key: str
    xml_tag: str
    values: object

    @property
    def omitted(self) -> bool:
        """Whether the field is left out of both representations.

        Returns
        -------
        bool
            True when there is no value: None or an empty list.
        """
        return self.values is None or (
            isinstance(self.values, list) and not self.values
        )

    def to_json(self) -> object:
        """Return the native JSON value of the field.

        Returns
        -------
        object
            The resolved values unchanged, unless a member converts them.
        """
        return self.values

    @abstractmethod
    def add_to_xml(self, root: Element) -> None:
        """Append or set the native XML form of the field on a query element.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """


class _TextsMember(_Member):
    """Repeated literal strings, one child element each."""

    def add_to_xml(self, root: Element) -> None:
        """Append one text child per value.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        _text_nodes(root, self.xml_tag, self.values)


class _TextMember(_Member):
    """One literal string: a JSON string and one child element."""

    def add_to_xml(self, root: Element) -> None:
        """Append one text child.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        _text_nodes(root, self.xml_tag, [self.values])


class _BooleanMember(_Member):
    """A boolean: a JSON boolean and a true/false child element."""

    def add_to_xml(self, root: Element) -> None:
        """Append one child holding true or false.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        _text_nodes(root, self.xml_tag, ["true" if self.values else "false"])


class _AttributeMember(_Member):
    """One scalar rendered as an XML attribute of the query element."""

    def add_to_xml(self, root: Element) -> None:
        """Set the attribute to the value's lexical form.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        root.set(self.xml_tag, str(self.values))


class _WeightMember(_Member):
    """A scoring weight: a JSON number and a native double XML attribute."""

    def add_to_xml(self, root: Element) -> None:
        """Set the weight attribute in the native double lexical form.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        root.set(self.xml_tag, _weight_text(self.values))


class _QueryMember(_Member):
    """One nested query, serialized in the format of its parent."""

    def to_json(self) -> object:
        """Serialize the nested query.

        Returns
        -------
        object
            The nested query's native representation.
        """
        return _subquery(self.values, "json")

    def add_to_xml(self, root: Element) -> None:
        """Append the nested query element directly.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        root.append(_subquery(self.values, "xml"))


class _WrappedQueryMember(_QueryMember):
    """One nested query inside a named XML wrapper, such as positive."""

    def add_to_xml(self, root: Element) -> None:
        """Append the nested query inside its wrapper element.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        wrapper = SubElement(root, f"{{{CTS_NS_URI}}}{self.xml_tag}")
        wrapper.append(_subquery(self.values, "xml"))


class _QueriesMember(_Member):
    """Several nested queries, appended directly in XML."""

    def to_json(self) -> object:
        """Serialize every nested query.

        Returns
        -------
        list
            The nested queries' native representations in order.
        """
        return [_subquery(query, "json") for query in self.values]

    def add_to_xml(self, root: Element) -> None:
        """Append every nested query element.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        root.extend([_subquery(query, "xml") for query in self.values])


class _QNamesMember(_Member):
    """Repeated QNames: Clark notation in JSON, prefixed text in XML."""

    def to_json(self) -> object:
        """Render the QNames in Clark notation.

        Returns
        -------
        list[str]
            ``{uri}local`` names, or bare local names without a namespace.
        """
        return [_clark(uri, local) for uri, local in self.values]

    def add_to_xml(self, root: Element) -> None:
        """Append one QName child per value.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        _qname_nodes(root, self.xml_tag, self.values)


class _QNameMember(_Member):
    """One QName: a Clark-notation JSON string and one child element."""

    def to_json(self) -> object:
        """Render the QName in Clark notation.

        Returns
        -------
        str
            ``{uri}local``, or the bare local name without a namespace.
        """
        return _clark(*self.values)

    def add_to_xml(self, root: Element) -> None:
        """Append the QName child.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        _qname_nodes(root, self.xml_tag, [self.values])


class _TypedMember(_Member):
    """Range values with their XML Schema types."""

    def to_json(self) -> object:
        """Render native type/value objects.

        Returns
        -------
        list[dict]
            ``{"type": ..., "val": ...}`` per value.
        """
        return [
            {"type": _JSON_RANGE_TYPES[atomic_type], "val": lexical}
            for atomic_type, lexical in self.values
        ]

    def add_to_xml(self, root: Element) -> None:
        """Append one child typed with xsi:type per value.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        for atomic_type, lexical in self.values:
            _typed_node(root, self.xml_tag, atomic_type, lexical)


class _JsonValuesMember(_Member):
    """JSON property values: strings, numbers and booleans."""

    def to_json(self) -> object:
        """Render the values as the JSON scalars MarkLogic matches.

        Returns
        -------
        list
            JSON strings, numbers and booleans.
        """
        return [
            _json_scalar(atomic_type, lexical) for atomic_type, lexical in self.values
        ]

    def add_to_xml(self, root: Element) -> None:
        """Append one child per value: strings untyped, numbers as xs:double.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        for atomic_type, lexical in self.values:
            _json_value_node(root, self.xml_tag, atomic_type, lexical)


class _RegionsMember(_Member):
    """Geospatial regions by their native text forms."""

    def to_json(self) -> object:
        """Render the regions' text forms.

        Returns
        -------
        list[str]
            Native region text, such as ``10,20``.
        """
        return [text for _, text in self.values]

    def add_to_xml(self, root: Element) -> None:
        """Append one child typed with its cts: region type per region.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        for region_type, text in self.values:
            child = SubElement(root, f"{{{CTS_NS_URI}}}{self.xml_tag}")
            child.set("xmlns:cts", CTS_NS_URI)
            child.set(f"{{{_XSI_NS_URI}}}type", f"cts:{region_type}")
            child.text = text


class _PeriodsMember(_Member):
    """Temporal periods with their start and end."""

    def to_json(self) -> object:
        """Render native start/end objects.

        Returns
        -------
        list[dict]
            ``{"periodStart": ..., "periodEnd": ...}`` per period.
        """
        return [{"periodStart": start, "periodEnd": end} for start, end in self.values]

    def add_to_xml(self, root: Element) -> None:
        """Append one period element per period.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        for start, end in self.values:
            period = SubElement(root, f"{{{CTS_NS_URI}}}{self.xml_tag}")
            SubElement(period, f"{{{CTS_NS_URI}}}period-start").text = start
            SubElement(period, f"{{{CTS_NS_URI}}}period-end").text = end


class _ReferencesMember(_Member):
    """Literal range-index references, each a complete native element."""

    def to_json(self) -> object:
        """Render every reference directly into native JSON.

        Returns
        -------
        list[dict]
            Native JSON references.

        Raises
        ------
        TypeError
            For an element-attribute reference: MarkLogic 12.1 cannot read its
            own JSON form back (XDMP-RANGEINDEXNODE), while XML works.
        """
        if any(name in _XML_ONLY_REFERENCES for name, _ in self.values):
            message = (
                "MarkLogic cannot read an element-attribute reference back from "
                "CTS JSON; serialize the query as XML or run it through eval"
            )
            raise TypeError(message)
        return [_render(name, members, "json") for name, members in self.values]

    def add_to_xml(self, root: Element) -> None:
        """Append every native reference element.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        root.extend([_render(name, members, "xml") for name, members in self.values])


class _TriplesMember(_Member):
    """RDF terms: IRIs, or typed literals with their datatype."""

    def to_json(self) -> object:
        """Render native RDF JSON terms.

        Returns
        -------
        list
            IRI strings, and ``{"datatype": ..., "value": ...}`` literals.
        """
        return [
            lexical
            if datatype is None
            else {
                "datatype": datatype,
                "value": _rdf_scalar(datatype, lexical),
            }
            for datatype, lexical in self.values
        ]

    def add_to_xml(self, root: Element) -> None:
        """Append native RDF terms with datatype attributes, not xsi:type.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        for datatype, lexical in self.values:
            child = SubElement(root, f"{{{CTS_NS_URI}}}{self.xml_tag}")
            if datatype is not None:
                child.set("datatype", datatype)
            child.text = lexical


class _NodesMember(_Member):
    """Literal XML or JSON model nodes."""

    def to_json(self) -> object:
        """Render XML strings or JSON model-node values directly into JSON.

        Returns
        -------
        list
            Fresh copies of the node values.
        """
        return [deepcopy(value) for value, _ in self.values]

    def add_to_xml(self, root: Element) -> None:
        """Append fresh model nodes inside native CTS wrappers.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        for value, is_xml in self.values:
            child = SubElement(root, f"{{{CTS_NS_URI}}}{self.xml_tag}")
            if not is_xml:
                child.text = json.dumps(
                    value,
                    ensure_ascii=False,
                    separators=(", ", ":"),
                )
            else:
                child.extend(_xml_model_nodes(value))


class _DistinctiveOptionsMember(_Member):
    """Distinctive-term options of a similar query, held as their XML element."""

    def to_json(self) -> object:
        """Render the options independently of their XML form.

        Returns
        -------
        dict
            Native JSON option members.

        Raises
        ------
        ValueError
            For an option without a native JSON form.
        """
        result = {}
        converters = {
            "score": str,
            "max-terms": int,
            "min-val": int,
            "min-weight": int,
            "complete": lambda text: text in {"true", "1"},
        }
        for child in self.values:
            if not isinstance(child.tag, str):
                continue
            name = child.tag.removeprefix("{cts:distinctive-terms}")
            if name not in converters:
                message = f"Unsupported local CTS distinctive-term option: {child.tag}"
                raise ValueError(message)
            result[_json_name(name)] = converters[name](child.text)
        return result

    def add_to_xml(self, root: Element) -> None:
        """Append a fresh copy of the options element.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        root.append(deepcopy(self.values))


class _ColumnMember(_Member):
    """A TDE column predicate with its name and column ID."""

    def to_json(self) -> object:
        """Render the column predicate.

        Returns
        -------
        list[dict]
            ``[{"column": ..., "columnID": ...}]``.
        """
        name, column_id = self.values
        return [{"column": name, "columnID": str(column_id)}]

    def add_to_xml(self, root: Element) -> None:
        """Append the column predicate element.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The query element.
        """
        name, column_id = self.values
        SubElement(
            root,
            f"{{{CTS_NS_URI}}}{self.xml_tag}",
            {"column": name, "columnID": str(column_id)},
        )



def _qname_nodes(root, tag, qnames):
    """Append one QName text child per name, declaring a prefix for a namespace.

    Parameters
    ----------
    root : xml.etree.ElementTree.Element
        The query element.
    tag : str
        Local name of the children in the cts namespace.
    qnames : list[tuple[str, str]]
        Namespace URI ('' for none) and local name of each QName.
    """
    for uri, local in qnames:
        child = SubElement(root, f"{{{CTS_NS_URI}}}{tag}")
        if uri:
            child.set(f"xmlns:{_QNAME_PREFIX}", uri)
            child.text = f"{_QNAME_PREFIX}:{local}"
        else:
            child.text = local


def _typed_node(root, tag, atomic_type, lexical):
    """Append a range value child typed with xsi:type.

    Parameters
    ----------
    root : xml.etree.ElementTree.Element
        The query element.
    tag : str
        Local name of the child in the cts namespace.
    atomic_type : str
        XML Schema type, such as xs:decimal.
    lexical : str
        The value's lexical form.
    """
    child = SubElement(root, f"{{{CTS_NS_URI}}}{tag}")
    child.set("xmlns:xs", _XS_NS_URI)
    child.set(f"{{{_XSI_NS_URI}}}type", atomic_type)
    child.text = lexical


def _json_value_node(root, tag, atomic_type, lexical):
    """Append a JSON property value: strings untyped, numbers as xs:double.

    Parameters
    ----------
    root : xml.etree.ElementTree.Element
        The query element.
    tag : str
        Local name of the child in the cts namespace.
    atomic_type : str
        XML Schema type of the literal value.
    lexical : str
        The value's lexical form.
    """
    if atomic_type == "xs:string":
        _text_nodes(root, tag, [lexical])
    elif atomic_type == "xs:boolean":
        _typed_node(root, tag, "xs:boolean", lexical)
    else:
        _typed_node(root, tag, "xs:double", lexical)


def _clark(uri, local):
    """Return the native JSON form of a QName in Clark notation.

    Parameters
    ----------
    uri : str
        Namespace URI; '' for none.
    local : str
        Local name.

    Returns
    -------
    str
        ``{uri}local``, or the bare local name without a namespace.
    """
    return f"{{{uri}}}{local}" if uri else local


def _json_scalar(atomic_type, lexical):
    """Return a JSON property value as the JSON scalar MarkLogic matches.

    MarkLogic compares JSON property numbers as doubles, so a decimal is sent
    as a float: digits beyond double precision are not significant to the
    match, and the standard JSON encoder cannot write a Decimal.

    Parameters
    ----------
    atomic_type : str
        XML Schema type of the literal value.
    lexical : str
        Its lexical form.

    Returns
    -------
    str, int, float or bool
        The JSON scalar.

    Raises
    ------
    ValueError
        For a type that is not a JSON string, number or boolean.
    """
    if atomic_type == "xs:string":
        return lexical
    if atomic_type == "xs:boolean":
        return lexical == "true"
    if atomic_type == "xs:integer":
        return int(lexical)
    if atomic_type in {"xs:decimal", "xs:double", "xs:float"}:
        return float(lexical)
    message = f"Unsupported local JSON property value type: {atomic_type}"
    raise ValueError(message)


def _texts_member(json_key, xml_tag, expression):
    """Describe repeated literal strings.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _TextsMember
        The described field; omitted when there are none.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    """
    with _error_context(json_key):
        return _TextsMember(json_key, xml_tag, _strings(expression))


def _value_texts_member(json_key, xml_tag, expression):
    """Describe value-query text; an omitted text matches any value ("*").

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _TextsMember
        The described field.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    """
    with _error_context(json_key):
        values = _strings(expression) if expression is not None else ["*"]
        return _TextsMember(json_key, xml_tag, values)


def _text_member(json_key, xml_tag, expression):
    """Describe one literal string, rendered as a single JSON string.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _TextMember
        The described field.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    ValueError
        If the argument does not hold exactly one value.
    """
    with _error_context(json_key):
        return _TextMember(json_key, xml_tag, _single(_strings(expression)))


def _attribute_member(json_key, xml_tag, expression):
    """Describe one literal string rendered as an XML attribute.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML attribute local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _AttributeMember
        The described field.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    ValueError
        If the argument does not hold exactly one value.
    """
    with _error_context(json_key):
        return _AttributeMember(json_key, xml_tag, _single(_strings(expression)))


def _weight_member(json_key, xml_tag, expression):
    """Describe an explicitly supplied scoring weight.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML attribute local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _WeightMember
        The described field; omitted when the expression is None.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    ValueError
        For a weight that is not finite.
    """
    with _error_context(json_key):
        values = _number(expression) if expression is not None else None
        return _WeightMember(json_key, xml_tag, values)


def _lexical_member(json_key, xml_tag, expression):
    """Describe one atomic value rendered by its lexical form, such as a timestamp.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _TextMember
        The described field; omitted when the expression is None.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    """
    with _error_context(json_key):
        values = _atomic(expression)[1] if expression is not None else None
        return _TextMember(json_key, xml_tag, values)


def _lexicals_member(json_key, xml_tag, expression):
    """Describe repeated atomic values rendered by their lexical forms.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _TextsMember
        The described field; omitted when there are none.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    """
    with _error_context(json_key):
        values = [_atomic(item)[1] for item in _sequence(expression)]
        return _TextsMember(json_key, xml_tag, values)


def _qnames_member(json_key, xml_tag, expression):
    """Describe repeated QNames.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _QNamesMember
        The described field; omitted when there are none.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    """
    with _error_context(json_key):
        values = [_qname(item) for item in _sequence(expression)]
        return _QNamesMember(json_key, xml_tag, values)


def _qname_member(json_key, xml_tag, expression):
    """Describe one QName, rendered as a single JSON string.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _QNameMember
        The described field.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    ValueError
        If the argument does not hold exactly one value.
    """
    with _error_context(json_key):
        values = _single([_qname(item) for item in _sequence(expression)])
        return _QNameMember(json_key, xml_tag, values)


def _typed_member(json_key, xml_tag, expression):
    """Describe range values with their XML Schema types.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _TypedMember
        The described field; omitted when there are none.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    """
    with _error_context(json_key):
        values = [_atomic(item) for item in _sequence(expression)]
        return _TypedMember(json_key, xml_tag, values)


def _json_values_member(json_key, xml_tag, expression):
    """Describe JSON property values: strings, numbers and booleans.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _JsonValuesMember
        The described field; omitted when there are none.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    """
    with _error_context(json_key):
        values = [_atomic(item) for item in _sequence(expression)]
        return _JsonValuesMember(json_key, xml_tag, values)


def _regions_member(json_key, xml_tag, expression):
    """Describe geospatial regions by their native text forms.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _RegionsMember
        The described field; omitted when there are none.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    """
    with _error_context(json_key):
        values = [_region(item) for item in _sequence(expression)]
        return _RegionsMember(json_key, xml_tag, values)


def _periods_member(json_key, xml_tag, expression):
    """Describe temporal periods by their start and end.

    Parameters
    ----------
    json_key : str
        Native JSON member name, also naming the argument in errors.
    xml_tag : str
        Native XML child element local name.
    expression : XqyExpression or None
        The query's converted argument.

    Returns
    -------
    _PeriodsMember
        The described field; omitted when there are none.

    Raises
    ------
    TypeError
        For an argument requiring server evaluation.
    """
    with _error_context(json_key):
        values = [_period(item) for item in _sequence(expression)]
        return _PeriodsMember(json_key, xml_tag, values)


def _query_member(json_key, xml_tag, expression):
    """Describe a nested query, serialized when the field is rendered.

    Parameters
    ----------
    json_key : str
        Native JSON member name.
    xml_tag : str
        Unused: the nested query element is appended directly.
    expression : XqyExpression
        The nested query.

    Returns
    -------
    _QueryMember
        The described field.
    """
    return _QueryMember(json_key, xml_tag, expression)


def _single(values):
    """Return the only item of a resolved sequence.

    Parameters
    ----------
    values : list
        Resolved values.

    Returns
    -------
    object
        The single value.

    Raises
    ------
    ValueError
        If the sequence does not contain exactly one item.
    """
    if len(values) != 1:
        message = "CTS argument requires exactly one value for local serialization."
        raise ValueError(message)
    return values[0]


def _atomic(expression):
    """Resolve a literal atomic value to its XML Schema type and lexical form.

    Parameters
    ----------
    expression : XqyExpression
        A bound Python literal; function calls require server evaluation.

    Returns
    -------
    tuple[str, str]
        Type name such as ``xs:integer`` and the lexical form.

    Raises
    ------
    TypeError
        For values requiring server evaluation.
    """
    if isinstance(expression, AtomicValue):
        value = expression.value
        lexical = ("true" if value else "false") if isinstance(value, bool) else value
        return expression.cast or "xs:string", lexical
    message = (
        "CTS value argument requires server evaluation, got "
        f"{_display(expression)}."
    )
    raise TypeError(message)


def _qname(expression):
    """Resolve a QName argument to its namespace URI and local name.

    Parameters
    ----------
    expression : XqyExpression
        ``xs:QName`` of an unprefixed name, or ``fn:QName(uri, name)``.

    Returns
    -------
    tuple[str, str]
        Namespace URI ('' for none) and local name.

    Raises
    ------
    TypeError
        For a prefixed xs:QName, whose namespace is only known from the
        compilation's bindings, or a value requiring server evaluation.
    """
    if (
        isinstance(expression, FunctionCall)
        and expression.fn == "xs:QName"
        and len(expression.args) == 1
    ):
        lexical = _single(_strings(expression.args[0]))
        if ":" in lexical:
            message = (
                "Prefixed CTS QNames require compilation namespace bindings; "
                "use fn.qname(uri, name) for local serialization."
            )
            raise TypeError(message)
        return "", lexical
    if (
        isinstance(expression, FunctionCall)
        and expression.fn == "fn:QName"
        and len(expression.args) == _QNAME_ARGUMENT_COUNT
    ):
        uri = _single(_strings(expression.args[0]))
        lexical = _single(_strings(expression.args[1]))
        return uri, lexical.rpartition(":")[2]
    message = (
        "CTS QName argument requires server evaluation, got "
        f"{_display(expression)}."
    )
    raise TypeError(message)


def _region(expression):
    """Resolve a literal point, box, circle or polygon to its native text form.

    Parameters
    ----------
    expression : XqyExpression
        A region value built by the cts builder.

    Returns
    -------
    tuple[str, str]
        Region type (point, box, circle or polygon) and its text form.

    Raises
    ------
    TypeError
        For other regions or values requiring server evaluation.
    """
    if not isinstance(expression, _Region):
        message = (
            "CTS region argument requires server evaluation, got "
            f"{_display(expression)}."
        )
        raise TypeError(message)
    return expression.region_type, expression.to_text()


def _point_text(expression):
    """Return the native ``latitude,longitude`` text of a literal point.

    Parameters
    ----------
    expression : XqyExpression
        A Point built by the cts builder.

    Returns
    -------
    str
        Point text.

    Raises
    ------
    TypeError
        For other expressions, a WKT point or coordinates requiring evaluation.
    """
    if not isinstance(expression, Point):
        message = (
            "CTS point argument requires server evaluation, got "
            f"{_display(expression)}."
        )
        raise TypeError(message)
    return expression.to_text()


def _coordinate(expression):
    """Format a literal coordinate or radius without a redundant fraction.

    Parameters
    ----------
    expression : XqyExpression
        A literal number, optionally cast to xs:float or xs:double.

    Returns
    -------
    str
        ``10`` for an integral value, otherwise the shortest float form.

    Raises
    ------
    TypeError
        For a number requiring server evaluation.
    ValueError
        For a value that is not finite.
    """
    value = _number(expression)
    return str(int(value)) if value.is_integer() else repr(value)


def _period(expression):
    """Resolve a literal period to its start and end lexical forms.

    Parameters
    ----------
    expression : XqyExpression
        A Period built by the cts builder.

    Returns
    -------
    tuple[str, str]
        Start and end lexical forms.

    Raises
    ------
    TypeError
        For other expressions or bounds requiring server evaluation.
    """
    if not isinstance(expression, Period):
        message = (
            "CTS period argument requires server evaluation, got "
            f"{_display(expression)}."
        )
        raise TypeError(message)
    return _atomic(expression.start)[1], _atomic(expression.end)[1]


def _references_member(key, expression):
    """Describe literal range-index references in their native vocabulary.

    Parameters
    ----------
    key : str
        Native JSON member name, also naming the argument in errors.
    expression : XqyExpression
        One reference or a sequence of them, built by the cts builder.

    Returns
    -------
    _ReferencesMember
        The described references.

    Raises
    ------
    TypeError
        For a reference requiring server evaluation or missing its type.
    ValueError
        For a reference option without a local form.
    """
    with _error_context(key):
        references = [_reference(item) for item in _sequence(expression)]
        return _ReferencesMember(key, "", references)


def _reference(expression):
    """Describe one literal reference without inferring its database index.

    Parameters
    ----------
    expression : XqyExpression
        A reference built by the cts builder.

    Returns
    -------
    tuple[str, list[_Member]]
        The reference's native local name and its described fields.

    Raises
    ------
    TypeError
        For an unsupported reference, a namespace map, a missing scalar type or
        coordinate system, or an argument requiring server evaluation.
    ValueError
        For a reference option without a local form.
    """
    if not isinstance(expression, FunctionCall):
        message = (
            "CTS reference argument requires server evaluation, "
            f"got {_display(expression)}."
        )
        raise TypeError(message)
    name = expression.fn.removeprefix("cts:")
    selectors = _REFERENCE_SELECTORS.get(name)
    if selectors is None:
        message = (
            "CTS reference argument requires server evaluation, "
            f"got {_display(expression)}."
        )
        raise TypeError(message)
    members = []
    for index, (key, tag, kind) in enumerate(selectors):
        value = expression.args[index]
        if kind == "qname":
            uri, local = _qname(value)
            prefix = "parent-" if key == "parent" else ""
            members.extend(
                [
                    _TextMember("parentNamespaceURI" if prefix else "namespaceURI",
                        prefix + "namespace-uri",
                        uri,
                    ),
                    _TextMember("parentLocalname" if prefix else "localname",
                        prefix + "localname",
                        local,
                    ),
                ],
            )
        else:
            members.append(_text_member(key, tag, value))
    options = _strings(expression.optionals[0]) if expression.optionals else []
    members.extend(_reference_options(name, options))
    if len(expression.optionals) > 1 and expression.optionals[1] is not None:
        message = (
            "CTS reference namespace maps cannot be serialized natively; "
            "use EQNames in the path or destination database namespaces."
        )
        raise TypeError(message)
    for index, (key, tag) in enumerate(
        [
            # MarkLogic writes geoHashPrecision but reads geohashPrecision.
            ("geohashPrecision", "geohash-precision"),
            ("units", "units"),
            ("invalidValues", "invalid-values"),
        ],
        start=2,
    ):
        if (
            len(expression.optionals) > index
            and expression.optionals[index] is not None
        ):
            members.append(_lexical_member(key, tag, expression.optionals[index]))
    return name, members


def _reference_options(name, options):
    """Describe explicit reference options without resolving a database index.

    Parameters
    ----------
    name : str
        Native local name of the reference, such as element-reference.
    options : list[str]
        Literal reference options.

    Returns
    -------
    list[_Member]
        Fields for the scalar type, collation, coordinate system and nullability.

    Raises
    ------
    TypeError
        If a range reference names no scalar type, or a region reference no
        coordinate system, so that only the server could resolve it.
    ValueError
        For an option without a local form.
    """
    members = []
    for option in options:
        if option in ("checked", "unchecked"):
            continue
        if option in ("nullable", "non-nullable"):
            members.append(
                _BooleanMember("nullable", "nullable", option == "nullable"),
            )
            continue
        key, _, value = option.partition("=")
        fields = {
            "type": ("scalarType", "scalar-type"),
            "collation": ("collation", "collation"),
            "coordinate-system": ("coordinateSystem", "coordinate-system"),
        }
        if key not in fields:
            message = f"Unsupported local CTS reference option: {option}"
            raise ValueError(message)
        json_key, tag = fields[key]
        members.append(_TextMember(json_key, tag, value))
    if name not in {"uri-reference", "collection-reference", "iri-reference"}:
        required = (
            "coordinateSystem"
            if name == "geospatial-region-path-reference"
            else "scalarType"
        )
        if not any(member.json_key == required for member in members):
            message = (
                f"CTS reference {required} requires an explicit option "
                "or server evaluation."
            )
            raise TypeError(message)
    return members


def _triples_member(tag, expression):
    """Describe RDF values, distinguishing IRIs from typed literals.

    Parameters
    ----------
    tag : str
        Native JSON member and XML child name, also naming the argument in errors.
    expression : XqyExpression
        Literal values or sem:iri calls.

    Returns
    -------
    _TriplesMember
        The described values; omitted when there are none.

    Raises
    ------
    TypeError
        For a value requiring server evaluation.
    """
    with _error_context(tag):
        values = []
        for item in _sequence(expression):
            if (
                isinstance(item, FunctionCall)
                and item.fn == "sem:iri"
                and len(item.args) == 1
                and not item.optionals
            ):
                values.append((None, _single(_strings(item.args[0]))))
            else:
                atomic_type, lexical = _atomic(item)
                datatype = _XS_NS_URI + "#" + atomic_type.removeprefix("xs:")
                values.append((datatype, lexical))
        return _TriplesMember(tag, tag, values)


def _rdf_scalar(datatype, lexical):
    """Keep JSON-native scalar types for RDF numeric and boolean literals.

    Parameters
    ----------
    datatype : str
        Full XML Schema datatype IRI.
    lexical : str
        The literal's lexical form.

    Returns
    -------
    str, int, float or bool
        A JSON number or boolean for those datatypes, else the lexical form.
    """
    atomic_type = "xs:" + datatype.rsplit("#", 1)[-1]
    if atomic_type in {
        "xs:integer",
        "xs:double",
        "xs:float",
        "xs:decimal",
        "xs:boolean",
    }:
        return _json_scalar(atomic_type, lexical)
    return lexical


def _triple_operators(expression):
    """Describe one object operator or the subject, predicate and object ones.

    Parameters
    ----------
    expression : XqyExpression or None
        Literal triple-range operators.

    Returns
    -------
    list[_AttributeMember]
        No fields, one object-operator field or three operator fields.

    Raises
    ------
    TypeError
        For operators requiring server evaluation.
    ValueError
        For two or more than three operators.
    """
    operators = _strings(expression)
    if not operators:
        return []
    if len(operators) == 1:
        return [_AttributeMember("objectOperator", "object-operator", operators[0])]
    if len(operators) != len(("subject", "predicate", "object")):
        message = "CTS triple operator requires one or three values."
        raise ValueError(message)
    return [
        _AttributeMember(key + "Operator", key + "-operator", operator)
        for key, operator in zip(("subject", "predicate", "object"), operators)
    ]


def _nodes_member(key, tag, expression):
    """Describe literal XML or JSON nodes given as xdmp:unquote calls.

    Parameters
    ----------
    key : str
        Native JSON member name, also naming the argument in errors.
    tag : str
        Native XML child local name.
    expression : XqyExpression
        Literal xdmp:unquote calls, optionally projected to their root element.

    Returns
    -------
    _NodesMember
        The described nodes.

    Raises
    ------
    TypeError
        For nodes requiring server evaluation.
    ValueError
        For invalid literal JSON.
    """
    with _error_context(key):
        return _NodesMember(key, tag, [_literal_node(x) for x in _sequence(expression)])


def _literal_node(expression):
    """Read literal XML or JSON data from an xdmp:unquote call.

    Parameters
    ----------
    expression : XqyExpression
        An xdmp:unquote call, optionally projected to its root element.

    Returns
    -------
    tuple[object, bool]
        The XML source text or decoded JSON value, and whether it is XML.

    Raises
    ------
    TypeError
        For other expressions, a DTD, or a JSON projection, which only the
        server can evaluate.
    ValueError
        For invalid literal JSON or XML that is not well-formed.
    """
    projected = (
        isinstance(expression, ResultXPath) and expression.source in {"*", "node()"}
    )
    inner = expression.inner if projected else expression
    if (
        not isinstance(inner, FunctionCall)
        or inner.fn != "xdmp:unquote"
        or len(inner.args) != 1
        or any(x is not None for x in inner.optionals)
    ):
        message = (
            "CTS node argument requires a literal xdmp:unquote call "
            "or server evaluation."
        )
        raise TypeError(message)
    source = _single(_strings(inner.args[0]))
    if not source.lstrip().startswith("<"):
        if projected and expression.source != "node()":
            message = "CTS JSON model-node projections require server evaluation."
            raise TypeError(message)
        return json.loads(source, parse_constant=_invalid_json_constant), False
    if "<!DOCTYPE" in source:
        message = "CTS literal XML with a DTD requires server evaluation."
        raise TypeError(message)
    try:
        document = minidom.parseString(source)
    except ExpatError as error:
        message = f"CTS literal XML is not well-formed: {error}"
        raise ValueError(message) from error
    with document:
        if projected:
            source = document.documentElement.toxml()
    return source, True


def _xml_model_nodes(source):
    """Parse XML model data without dropping prolog nodes or namespace bindings.

    Parameters
    ----------
    source : str
        Literal XML, possibly several top-level nodes.

    Returns
    -------
    list[xml.etree.ElementTree.Element]
        The parsed top-level nodes, comments and processing instructions.

    Raises
    ------
    TypeError
        For an nsN prefix, which ElementTree would rename.
    """
    content = re.sub(r"^\s*<\?xml\s.*?\?>", "", source, count=1)
    pending = []
    parsed = iterparse(
        StringIO("<nodes>" + content + "</nodes>"),
        events=("start", "start-ns"),
        parser=XMLParser(target=TreeBuilder(insert_comments=True, insert_pis=True)),
    )
    for event, value in parsed:
        if event == "start-ns":
            prefix, uri = value
            if re.fullmatch(r"ns[0-9]+", prefix):
                message = (
                    "CTS XML namespace prefixes nsN conflict with ElementTree; "
                    "use named prefixes or server evaluation."
                )
                raise TypeError(message)
            pending.append(("xmlns:" + prefix if prefix else "xmlns", uri))
        else:
            for attribute, uri in pending:
                value.set(attribute, uri)
            pending.clear()
    return list(parsed.root)


def _invalid_json_constant(value):
    """Reject non-JSON numeric extensions accepted by the standard decoder.

    Parameters
    ----------
    value : str
        The constant, such as NaN or Infinity.

    Raises
    ------
    ValueError
        Always: native JSON has no such constant.
    """
    message = f"Invalid CTS model-node JSON constant: {value}"
    raise ValueError(message)


def _distinctive_options_member(expression):
    """Describe the literal distinctive-term options of a similar query.

    Parameters
    ----------
    expression : XqyExpression or None
        A projected xdmp:unquote call of a cts:distinctive-terms options element.

    Returns
    -------
    _DistinctiveOptionsMember
        The described options; omitted when the expression is None.

    Raises
    ------
    ValueError
        For anything but a projected XML options element.
    TypeError
        For options requiring server evaluation.
    """
    with _error_context("options"):
        value, is_xml = (
            _literal_node(expression) if expression is not None else (None, False)
        )
        node = _single(_xml_model_nodes(value)) if is_xml else None
        if expression is not None and (
            node is None
            or node.tag != "{cts:distinctive-terms}options"
            or not isinstance(expression, ResultXPath)
        ):
            message = (
                "CTS similar options must be an XML cts:distinctive-terms "
                "options element."
            )
            raise ValueError(message)
        return _DistinctiveOptionsMember("options", "", node)


_XML_ONLY_REFERENCES = frozenset({"element-attribute-reference"})
_REFERENCE_SELECTORS = {
    "element-reference": [("", "", "qname")],
    "element-attribute-reference": [("parent", "", "qname"), ("", "", "qname")],
    "path-reference": [("pathExpression", "path-expression", "text")],
    "field-reference": [("fieldName", "field-name", "text")],
    "json-property-reference": [("property", "property", "text")],
    "uri-reference": [],
    "collection-reference": [],
    "iri-reference": [],
    "geospatial-region-path-reference": [("pathExpression", "path-expression", "text")],
}


_RANGE_OPERATORS = frozenset({"<", "<=", ">", ">=", "=", "!="})
_ORDER_OPTIONS = frozenset({"ordered", "unordered"})
_OR_OPTIONS = frozenset({"synonym"})
# Probed on MarkLogic 12.1: cts:period-compare-query accepts exactly these.
_TEMPORAL_OPERATORS = frozenset(
    {
        "aln_after",
        "aln_before",
        "aln_contained_by",
        "aln_contains",
        "aln_equals",
        "aln_finished_by",
        "aln_finishes",
        "aln_meets",
        "aln_met_by",
        "aln_overlapped_by",
        "aln_overlaps",
        "aln_started_by",
        "aln_starts",
        "iso_contains",
        "iso_equals",
        "iso_imm_precedes",
        "iso_imm_succeeds",
        "iso_overlaps",
        "iso_precedes",
        "iso_succeeds",
    },
)
_DIRECTORY_DEPTHS = frozenset({"1", "infinity"})


def _operator_argument(value, *, required: bool = True) -> XqyExpression | None:
    """Validate a range comparison operator, preserving expression composition.

    Parameters
    ----------
    value : str | XqyExpression | None
        Literal comparison operator or an expression evaluated by MarkLogic.
    required : bool, default True
        Whether None is invalid. False preserves None as an omitted argument.

    Returns
    -------
    XqyExpression | None
        Validated operator expression, or None for an omitted optional operator.

    Raises
    ------
    ValueError
        For an unsupported literal or a missing required operator.
    """
    if value is None and not required:
        return None
    if isinstance(value, XqyExpression):
        return value
    if not isinstance(value, str) or value not in _RANGE_OPERATORS:
        message = f"unsupported range operator: {value!r}"
        raise ValueError(message)
    return _as_expr(value, cast="xs:string")


def _choice_options_argument(
    options,
    allowed: frozenset[str],
    query_name: str,
) -> XqyExpression | None:
    """Validate literal options of a query that takes at most one of a few.

    Parameters
    ----------
    options : str | list[str] | XqyExpression | None
        Literal options or an expression evaluated by MarkLogic.
    allowed : frozenset[str]
        Native options of the query.
    query_name : str
        The native query, such as and-query, named in errors.

    Returns
    -------
    XqyExpression | None
        The converted options, or None when omitted.

    Raises
    ------
    ValueError
        For literal options MarkLogic rejects: an unknown option or several.
    """
    literal = _literal_strings(options)
    if literal is not None:
        _check_choice_options(literal, allowed, query_name)
    return _optional(options)


def _check_choice_options(
    options: list[str],
    allowed: frozenset[str],
    query_name: str,
):
    """Reject options MarkLogic does not accept for a query (XDMP-OPTION).

    Parameters
    ----------
    options : list[str]
        Literal options.
    allowed : frozenset[str]
        Native options of the query; at most one may be given.
    query_name : str
        The native query, such as and-query, named in errors.

    Raises
    ------
    ValueError
        For an unknown option or several options.
    """
    if len(options) > 1 or any(option not in allowed for option in options):
        message = (
            f"options {options!r} are not {query_name} options; use at most one "
            f"of {', '.join(sorted(allowed))}"
        )
        raise ValueError(message)


def _near_options_argument(options) -> XqyExpression | None:
    """Validate literal near-query options.

    Parameters
    ----------
    options : str | list[str] | XqyExpression | None
        Literal options or an expression evaluated by MarkLogic.

    Returns
    -------
    XqyExpression | None
        The converted options, or None when omitted.

    Raises
    ------
    ValueError
        For unsupported, malformed or repeated literal options.
    """
    literal = _literal_strings(options)
    if literal is not None:
        _near_options(literal)
    return _optional(options)


def _temporal_operator_argument(value) -> XqyExpression:
    """Validate a literal temporal operator; expressions stay composable.

    Parameters
    ----------
    value : str | XqyExpression
        A native temporal operator, such as aln_contains, or an expression.

    Returns
    -------
    XqyExpression
        The converted operator.

    Raises
    ------
    ValueError
        For a literal that is not a native temporal operator.
    """
    if isinstance(value, str) and value not in _TEMPORAL_OPERATORS:
        message = f"unsupported temporal operator: {value!r}"
        raise ValueError(message)
    return _as_expr(value)


def _literal_strings(value) -> list[str] | None:
    """Return literal option strings, or None for anything else.

    Parameters
    ----------
    value : object
        A supplied options argument.

    Returns
    -------
    list[str] | None
        The strings of a literal string or list of strings; None otherwise.
    """
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)) and all(isinstance(v, str) for v in value):
        return list(value)
    return None


def _depth_argument(value) -> XqyExpression:
    """Validate a literal directory depth; expressions stay composable.

    Parameters
    ----------
    value : str | XqyExpression
        ``"1"``, ``"infinity"`` or an expression evaluated by MarkLogic.

    Returns
    -------
    XqyExpression
        The depth as an ``xs:string`` value, or the expression unchanged.

    Raises
    ------
    ValueError
        For any other literal depth.
    """
    if isinstance(value, XqyExpression):
        return value
    if value not in _DIRECTORY_DEPTHS:
        message = f"directory depth must be '1' or 'infinity': {value!r}"
        raise ValueError(message)
    return _as_expr(value, cast="xs:string")


def _optional(value) -> XqyExpression | None:
    """Convert an optional argument; None marks it omitted.

    Parameters
    ----------
    value : AtomicInput | None
        A supplied argument or None.

    Returns
    -------
    XqyExpression | None
        The converted argument, or None when omitted.
    """
    return _as_expr(value) if value is not None else None


def _optional_double(value) -> XqyExpression | None:
    """Convert an optional numeric argument to the native double type.

    Parameters
    ----------
    value : float | XqyExpression | None
        A supplied weight or distance, or None.

    Returns
    -------
    XqyExpression | None
        The argument cast to ``xs:double``, or None when omitted.
    """
    return _as_expr(value, cast="xs:double") if value is not None else None


@contextmanager
def _error_context(label: str):
    """Prefix serialization errors raised inside the block with where they arose.

    Parameters
    ----------
    label : str
        The native function or argument being serialized.

    Yields
    ------
    None
        Control to the serializing block.

    Raises
    ------
    TypeError, ValueError
        The error raised in the block, or for a subclass such as a JSON decode
        error its base class, with the message prefixed with ``label`` and the
        original error chained as the cause.
    """
    try:
        yield
    except (TypeError, ValueError) as error:
        message = f"{label}: {error}"
        base = TypeError if isinstance(error, TypeError) else ValueError
        raise base(message) from error


def _operands(query: CtsQuery, kind: type[AndQuery | OrQuery]) -> list:
    """Return the queries an operator combines on its left-hand side.

    Parameters
    ----------
    query : CtsQuery
        The left-hand operand.
    kind : type[AndQuery] or type[OrQuery]
        The query the operator builds.

    Returns
    -------
    list
        The subqueries of a query of that kind without options, otherwise
        the query itself.
    """
    if isinstance(query, kind) and query.options is None:
        return _sequence(query.queries)
    return [query]


def _display(expression: object) -> str:
    """Show a converted argument the way it was supplied.

    Parameters
    ----------
    expression : object
        A field value: an expression, a nested query or another value.

    Returns
    -------
    str
        A literal for literal values, casts unwrapped; ``prefix:name(...)``
        for other function calls; ``[...]`` for sequences.
    """
    if isinstance(expression, AtomicValue):
        return _display_atomic(expression)
    if isinstance(expression, XqySequence):
        return "[" + ", ".join(_display(item) for item in expression.items) + "]"
    if isinstance(expression, FunctionCall):
        return _display_call(expression)
    return repr(expression)


def _display_atomic(value: AtomicValue) -> str:
    """Show a bound literal as the Python value it came from.

    Parameters
    ----------
    value : AtomicValue
        A bound literal.

    Returns
    -------
    str
        Numbers and booleans unquoted, strings quoted, other types as
        ``xs:type('lexical')``.
    """
    if value.cast in _UNQUOTED_CASTS or isinstance(value.value, bool):
        return str(value.value)
    if value.cast in (None, "xs:string"):
        return repr(value.value)
    return f"{value.cast}({value.value!r})"


def _display_call(call: FunctionCall) -> str:
    """Show a function call, unwrapping the casts arguments are converted with.

    Parameters
    ----------
    call : FunctionCall
        A call held as an argument.

    Returns
    -------
    str
        The cast argument itself, or ``prefix:name(arguments)``.
    """
    if call.fn in _DISPLAY_TRANSPARENT_CASTS and len(call.args) == 1:
        return _display(call.args[0])
    arguments = [*call.args, *(item for item in call.optionals if item is not None)]
    return f"{call.fn}({', '.join(_display(item) for item in arguments)})"
