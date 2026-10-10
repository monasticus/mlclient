"""Build structured queries using the JSON and XML Search API vocabulary."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import MISSING, Field as DataclassField, dataclass, field, fields
from datetime import date, datetime
from decimal import Decimal
from types import MappingProxyType
from typing import ClassVar, Literal, TypeVar, get_args
from xml.etree.ElementTree import Element as XmlElement, register_namespace

from mlclient.search.base import QueryComponent, SearchQuery

SEARCH_NS_URI = "http://marklogic.com/appservices/search"
"""Namespace URI for structured queries and Search API options."""
# ElementTree has no per-call prefix map; registering the prefix makes every
# serialized query and options element read search: instead of ns0:.
register_namespace("search", SEARCH_NS_URI)

__all__ = [
    "SEARCH_NS_URI",
    "AndNotQuery",
    "AndQuery",
    "Attribute",
    "BoostQuery",
    "Box",
    "Circle",
    "CollectionConstraintQuery",
    "CollectionQuery",
    "ContainerConstraintQuery",
    "ContainerQuery",
    "CustomConstraintQuery",
    "DirectoryQuery",
    "DocumentFragmentQuery",
    "DocumentQuery",
    "Element",
    "ElementConstraintQuery",
    "FalseQuery",
    "Field",
    "GeoAttributePairQuery",
    "GeoElementPairQuery",
    "GeoElementQuery",
    "GeoJsonPropertyPairQuery",
    "GeoJsonPropertyQuery",
    "GeoPathQuery",
    "GeoRegionConstraintQuery",
    "GeoRegionPathQuery",
    "GeospatialConstraintQuery",
    "JsonProperty",
    "LocksFragmentQuery",
    "LsqtQuery",
    "NearQuery",
    "NotInQuery",
    "NotQuery",
    "OperatorState",
    "OrQuery",
    "PathIndex",
    "Period",
    "PeriodCompareQuery",
    "PeriodRangeQuery",
    "Point",
    "Polygon",
    "PropertiesConstraintQuery",
    "PropertiesFragmentQuery",
    "QtextQuery",
    "Query",
    "QueryTarget",
    "RangeConstraintQuery",
    "RangeQuery",
    "Region",
    "StructuredQuery",
    "StructuredQueryBuilder",
    "TermQuery",
    "TrueQuery",
    "ValueConstraintQuery",
    "ValueQuery",
    "WordConstraintQuery",
    "WordQuery",
    "sq",
]

# MarkLogic's REST converter, json:config("custom"), keeps a bare text value of
# a member inside a queries array under this key.
_TEXT_VALUE_KEY = "_value"

_Scalar = str | int | float | bool | Decimal | date | datetime
_RESERVED_PREFIXES = frozenset({"", "search", "xml", "xmlns"})
_GeospatialOperator = Literal[
    "contains",
    "covered-by",
    "covers",
    "crosses",
    "disjoint",
    "equals",
    "intersects",
    "overlaps",
    "touches",
    "within",
]
_SCALAR_TYPES = get_args(_Scalar)
_TemporalOperator = Literal[
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
]
_Item = TypeVar("_Item")


class _Validated:
    """Freeze and validate a structured component's arguments when it is built.

    List arguments are stored as tuples and mappings as read-only copies, so
    components cannot change after they are built and a list compares equal
    to the same tuple. Numeric options such as weights,
    distances and coordinates must be finite; fields named in
    ``_VALUE_FIELDS`` hold search values, which may be INF or NaN.
    """

    _VALUE_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self):
        """Freeze list arguments, then reject invalid ones.

        Raises
        ------
        TypeError
            For a missing required argument, an unordered set where values or a
            sequence belong, or an argument of an unsupported type.
        ValueError
            For a non-finite numeric option, or invalid selectors, options or
            values.
        """
        for item in fields(self):
            value = getattr(self, item.name)
            if value is None and _is_required(item):
                message = f"{type(self).__name__}.{item.name} is required"
                raise TypeError(message)
            if isinstance(value, (set, frozenset)):
                message = (
                    f"{type(self).__name__}.{item.name} must be a value or a "
                    f"sequence, got {type(value).__name__}"
                )
                raise TypeError(message)
            if isinstance(value, list):
                object.__setattr__(self, item.name, tuple(value))
            elif isinstance(value, Mapping):
                object.__setattr__(self, item.name, MappingProxyType(dict(value)))
            elif item.name not in self._VALUE_FIELDS and _is_non_finite(value):
                message = f"{type(self).__name__}.{item.name} must be finite."
                raise ValueError(message)
        self._validate()

    def _validate(self):
        """Reject invalid arguments; components without constraints accept all."""


class StructuredQuery(SearchQuery, _Validated):
    """Represent a locally serializable Search API query, not an XQuery expression."""

    def __and__(self, other: StructuredQuery) -> AndQuery:
        """Match both queries: ``a & b`` is ``AndQuery((a, b))``.

        Parameters
        ----------
        other : StructuredQuery
            The other query.

        Returns
        -------
        AndQuery
            The intersection; an unordered and-query on the left is extended,
            so ``a & b & c`` holds all three queries.
        """
        if not isinstance(other, StructuredQuery):
            return NotImplemented
        unordered_and = isinstance(self, AndQuery) and self.ordered is None
        left = self.queries if unordered_and else self
        return AndQuery((*_sequence(left), other))

    def __or__(self, other: StructuredQuery) -> OrQuery:
        """Match either query: ``a | b`` is ``OrQuery((a, b))``.

        Parameters
        ----------
        other : StructuredQuery
            The other query.

        Returns
        -------
        OrQuery
            The union; an or-query on the left is extended, so ``a | b | c``
            holds all three queries.
        """
        if not isinstance(other, StructuredQuery):
            return NotImplemented
        left = self.queries if isinstance(self, OrQuery) else self
        return OrQuery((*_sequence(left), other))

    def __invert__(self) -> NotQuery:
        """Match what this query does not: ``~a`` is ``NotQuery(a)``.

        Returns
        -------
        NotQuery
            The negation.
        """
        return NotQuery(self)

    def to_combined_query(self) -> dict:
        """Wrap this structured query in a JSON combined query.

        Returns
        -------
        dict
            ``{"search": {"query": ...}}``. A subquery other than Query is
            wrapped in a Query first, as the Search API requires.

        """
        query = self if isinstance(self, Query) else Query(self)
        return {"search": query.to_json()}


class QueryTarget(QueryComponent, _Validated):
    """Describe an XML element, JSON property, field, or path range index."""


@dataclass(frozen=True)
class Element(QueryTarget):
    """Identify an XML element by its local name and namespace URI.

    Parameters
    ----------
    name : str
        Element local name.
    ns : str, default ''
        Element namespace URI.
    """

    name: str
    ns: str = ""

    def _validate(self):
        """Reject arguments that cannot form a native element.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_type(self, "name", str)
        _check_type(self, "ns", str, optional=True)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native element in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native element.
        """
        return _node(
            "element",
            attributes={"name": self.name, "ns": self.ns},
            output_format=output_format,
        )


@dataclass(frozen=True)
class Attribute(QueryComponent, _Validated):
    """Identify an attribute of the XML elements selected by a query.

    Parameters
    ----------
    name : str
        Attribute local name.
    ns : str, default ''
        Attribute namespace URI.
    """

    name: str
    ns: str = ""

    def _validate(self):
        """Reject arguments that cannot form a native attribute.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_type(self, "name", str)
        _check_type(self, "ns", str, optional=True)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native attribute in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native attribute.
        """
        return _node(
            "attribute",
            attributes={"name": self.name, "ns": self.ns},
            output_format=output_format,
        )


@dataclass(frozen=True)
class Field(QueryTarget):
    """Identify a database field.

    Parameters
    ----------
    name : str
        Configured field name.
    collation : str or None, default None
        Optional field collation URI.
    """

    name: str
    collation: str | None = None

    def _validate(self):
        """Reject arguments that cannot form a native field.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_type(self, "name", str)
        _check_type(self, "collation", str, optional=True)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native field in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native field.
        """
        attributes = {"name": self.name}
        if self.collation is not None:
            attributes["collation"] = self.collation
        return _node("field", attributes=attributes, output_format=output_format)


@dataclass(frozen=True)
class JsonProperty(QueryTarget):
    """Identify a JSON property regardless of the query serialization format.

    Parameters
    ----------
    name : str
        JSON property name.
    """

    name: str

    def _validate(self):
        """Reject arguments that cannot form a native json-property.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_type(self, "name", str)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native json-property in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native json-property.
        """
        return _node("json-property", text=self.name, output_format=output_format)


@dataclass(frozen=True)
class PathIndex(QueryTarget):
    """Identify a configured path range index with namespace bindings.

    Parameters
    ----------
    path : str
        Indexed XPath expression.
    namespaces : Mapping[str, str], optional
        Prefix-to-URI bindings used by the path expression.
    """

    path: str
    namespaces: Mapping[str, str] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Hash the path with its namespace bindings.

        Returns
        -------
        int
            A hash consistent with equality.
        """
        return hash((self.path, frozenset(self.namespaces.items())))

    def _validate(self):
        """Reject prefixes that would rebind a namespace serialization relies on.

        Raises
        ------
        ValueError
            For an empty prefix, or for search, xml or xmlns: binding search
            would move the path-index element itself to another namespace.
        """
        if any(prefix in _RESERVED_PREFIXES for prefix in self.namespaces):
            message = (
                "PathIndex namespace prefixes must be non-empty and not search, "
                "xml or xmlns."
            )
            raise ValueError(message)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native path-index in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native path-index.
        """
        if output_format == "json":
            value = {"text": self.path}
            if self.namespaces:
                value["namespaces"] = dict(self.namespaces)
            return {"path-index": value}
        attributes = {
            f"xmlns:{prefix}": uri for (prefix, uri) in self.namespaces.items()
        }
        return _node(
            "path-index",
            attributes=attributes,
            text=self.path,
            output_format=output_format,
        )


@dataclass(frozen=True)
class Query(StructuredQuery):
    """Wrap one or more subqueries for the Search API.

    Parameters
    ----------
    queries : StructuredQuery or Sequence[StructuredQuery]
        Subqueries the Search API ANDs together.
    """

    queries: StructuredQuery | Sequence[StructuredQuery]

    def _validate(self):
        """Reject arguments that cannot form a native query.

        Raises
        ------
        TypeError
            If a subquery is not a StructuredQuery or is a Query wrapper.
        """
        _check_subqueries(self.queries)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native query.
        """
        return _queries_node(
            "query",
            _subqueries(self.queries, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class AndQuery(StructuredQuery):
    """Combine subqueries using intersection.

    Parameters
    ----------
    queries : StructuredQuery or Sequence[StructuredQuery]
        Subqueries that must all match; an empty AND matches all.
    ordered : bool or None, default None
        Whether matches must occur in subquery order.
    """

    queries: StructuredQuery | Sequence[StructuredQuery]
    ordered: bool | None = None

    def _validate(self):
        """Reject arguments that cannot form a native and-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a subquery is not a StructuredQuery or is a Query wrapper.
        """
        _check_type(self, "ordered", bool, optional=True)
        _check_subqueries(self.queries)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native and-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native and-query.
        """
        return _queries_node(
            "and-query",
            _subqueries(self.queries, output_format=output_format)
            + _optional_children(ordered=self.ordered, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class OrQuery(StructuredQuery):
    """Combine subqueries using union.

    Parameters
    ----------
    queries : StructuredQuery or Sequence[StructuredQuery]
        Subqueries of which one must match; an empty OR matches none.
    """

    queries: StructuredQuery | Sequence[StructuredQuery]

    def _validate(self):
        """Reject arguments that cannot form a native or-query.

        Raises
        ------
        TypeError
            If a subquery is not a StructuredQuery or is a Query wrapper.
        """
        _check_subqueries(self.queries)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native or-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native or-query.
        """
        return _queries_node(
            "or-query",
            _subqueries(self.queries, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class AndNotQuery(StructuredQuery):
    """Exclude fragments matching the negative query.

    Parameters
    ----------
    positive : StructuredQuery
        Query selecting matches.
    negative : StructuredQuery
        Secondary query.
    """

    positive: StructuredQuery
    negative: StructuredQuery

    def _validate(self):
        """Reject arguments that cannot form a native and-not-query.

        Raises
        ------
        TypeError
            If a subquery is not a StructuredQuery or is a Query wrapper.
        """
        _check_subqueries(self.positive)
        _check_subqueries(self.negative)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native and-not-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native and-not-query.
        """
        return _query_pair(
            "and-not-query",
            ("positive-query", self.positive),
            ("negative-query", self.negative),
            output_format=output_format,
        )


@dataclass(frozen=True)
class NotInQuery(StructuredQuery):
    """Exclude positional overlaps with the negative query.

    Parameters
    ----------
    positive : StructuredQuery
        Query selecting matches.
    negative : StructuredQuery
        Secondary query.
    """

    positive: StructuredQuery
    negative: StructuredQuery

    def _validate(self):
        """Reject arguments that cannot form a native not-in-query.

        Raises
        ------
        TypeError
            If a subquery is not a StructuredQuery or is a Query wrapper.
        """
        _check_subqueries(self.positive)
        _check_subqueries(self.negative)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native not-in-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native not-in-query.
        """
        return _query_pair(
            "not-in-query",
            ("positive-query", self.positive),
            ("negative-query", self.negative),
            output_format=output_format,
        )


@dataclass(frozen=True)
class BoostQuery(StructuredQuery):
    """Boost matches using a secondary query.

    Parameters
    ----------
    matching : StructuredQuery
        Query selecting matches.
    boosting : StructuredQuery
        Secondary query.
    """

    matching: StructuredQuery
    boosting: StructuredQuery

    def _validate(self):
        """Reject arguments that cannot form a native boost-query.

        Raises
        ------
        TypeError
            If a subquery is not a StructuredQuery or is a Query wrapper.
        """
        _check_subqueries(self.matching)
        _check_subqueries(self.boosting)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native boost-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native boost-query.
        """
        return _query_pair(
            "boost-query",
            ("matching-query", self.matching),
            ("boosting-query", self.boosting),
            output_format=output_format,
        )


@dataclass(frozen=True)
class _SubqueryWrapper(StructuredQuery):
    """Wrap one subquery in the native node named by ``_NODE``.

    Parameters
    ----------
    query : StructuredQuery
        Wrapped subquery.
    """

    _NODE: ClassVar[str]

    query: StructuredQuery

    def _validate(self):
        """Reject a subquery the native wrapper node cannot hold.

        Raises
        ------
        TypeError
            If the subquery is not a StructuredQuery or is a Query wrapper.
        """
        _check_subqueries(self.query)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native wrapper node in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native wrapper node holding the serialized subquery.
        """
        return _node(
            self._NODE,
            _subqueries(self.query, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class NotQuery(_SubqueryWrapper):
    """Wrap a subquery in a not-query, matching what it does not match.

    Parameters
    ----------
    query : StructuredQuery
        Subquery to negate.
    """

    _NODE: ClassVar[str] = "not-query"


@dataclass(frozen=True)
class DocumentFragmentQuery(_SubqueryWrapper):
    """Wrap a subquery in a document-fragment-query.

    Parameters
    ----------
    query : StructuredQuery
        Subquery restricted to document fragments.
    """

    _NODE: ClassVar[str] = "document-fragment-query"


@dataclass(frozen=True)
class LocksFragmentQuery(_SubqueryWrapper):
    """Wrap a subquery in a locks-fragment-query.

    Parameters
    ----------
    query : StructuredQuery
        Subquery restricted to locks fragments.
    """

    _NODE: ClassVar[str] = "locks-fragment-query"


@dataclass(frozen=True)
class PropertiesFragmentQuery(_SubqueryWrapper):
    """Wrap a subquery in a properties-fragment-query.

    Parameters
    ----------
    query : StructuredQuery
        Subquery restricted to properties fragments.
    """

    _NODE: ClassVar[str] = "properties-fragment-query"


@dataclass(frozen=True)
class TrueQuery(StructuredQuery):
    """Match all fragments."""

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native true-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native true-query.
        """
        return _node("true-query", output_format=output_format)


@dataclass(frozen=True)
class FalseQuery(StructuredQuery):
    """Match no fragments."""

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native false-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native false-query.
        """
        return _node("false-query", output_format=output_format)


@dataclass(frozen=True)
class CollectionQuery(StructuredQuery):
    """Select documents by collection URI.

    Parameters
    ----------
    uris : str or Sequence[str]
        URIs to match.
    """

    uris: str | Sequence[str]

    def _validate(self):
        """Reject arguments that cannot form a native collection-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_types(self, "uris", str)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native collection-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native collection-query.
        """
        return _node(
            "collection-query",
            _children("uri", self.uris, json_array=True, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class DirectoryQuery(StructuredQuery):
    """Select documents by directory URI.

    Parameters
    ----------
    uris : str or Sequence[str]
        URIs to match.
    infinite : bool or None, default None
        Recurse into subdirectories. The server default is true.
    """

    uris: str | Sequence[str]
    infinite: bool | None = None

    def _validate(self):
        """Reject arguments that cannot form a native directory-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        ValueError
            If a directory URI does not end with a forward slash.
        """
        _check_type(self, "infinite", bool, optional=True)
        if any(not uri.endswith("/") for uri in _sequence(self.uris)):
            message = "Directory URIs must end with a forward slash."
            raise ValueError(message)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native directory-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native directory-query.
        """
        return _node(
            "directory-query",
            _children("uri", self.uris, json_array=True, output_format=output_format)
            + _optional_children(infinite=self.infinite, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class DocumentQuery(StructuredQuery):
    """Select documents by document URI.

    Parameters
    ----------
    uris : str or Sequence[str]
        URIs to match.
    """

    uris: str | Sequence[str]

    def _validate(self):
        """Reject arguments that cannot form a native document-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_types(self, "uris", str)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native document-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native document-query.
        """
        return _node(
            "document-query",
            _children("uri", self.uris, json_array=True, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class NearQuery(StructuredQuery):
    """Require subquery matches to occur within a word-distance interval.

    Parameters
    ----------
    queries : StructuredQuery or Sequence[StructuredQuery]
        Subqueries whose matches must occur near each other.
    distance : int or None, default None
        Maximum word distance. The server default is 10.
    minimum_distance : int or None, default None
        Minimum word distance. The server default is 0.
    distance_weight : float or None, default None
        Weight given to proximity.
    ordered : bool or None, default None
        Whether matches must occur in subquery order.
    """

    queries: StructuredQuery | Sequence[StructuredQuery]
    distance: int | None = None
    minimum_distance: int | None = None
    distance_weight: float | None = None
    ordered: bool | None = None

    def _validate(self):
        """Reject arguments that cannot form a native near-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a subquery is not a StructuredQuery or is a Query wrapper.
        """
        _check_number(self, "distance", integer=True, optional=True)
        _check_number(self, "minimum_distance", integer=True, optional=True)
        _check_number(self, "distance_weight", optional=True)
        _check_type(self, "ordered", bool, optional=True)
        _check_subqueries(self.queries)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native near-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native near-query.
        """
        return _queries_node(
            "near-query",
            _subqueries(self.queries, output_format=output_format)
            + _optional_children(
                distance=self.distance,
                minimum_distance=self.minimum_distance,
                distance_weight=self.distance_weight,
                ordered=self.ordered,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class TermQuery(StructuredQuery):
    """Match terms or phrases anywhere in the current search scope.

    Parameters
    ----------
    text : str or Sequence[str]
        Terms or phrases; multiple terms are ORed.
    weight : float or None, default None
        Contribution to the relevance score.
    options : str or Sequence[str], optional
        Native term options.
    """

    text: str | Sequence[str]
    weight: float | None = None
    options: str | Sequence[str] = ()

    def _validate(self):
        """Reject arguments that cannot form a native term-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_types(self, "text", str)
        _check_number(self, "weight", optional=True)
        _check_types(self, "options", str)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native term-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native term-query.
        """
        return _node(
            "term-query",
            _children("text", self.text, json_array=True, output_format=output_format)
            + _optional_children(weight=self.weight, output_format=output_format)
            + _children(
                "term-option",
                self.options,
                json_array=True,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class ContainerQuery(StructuredQuery):
    """Match a subquery within selected XML elements or JSON properties.

    Parameters
    ----------
    target : Element or JsonProperty or Sequence
        Element or JSON property descriptors.
    query : StructuredQuery
        Subquery to evaluate inside the container.
    fragment_scope : {'documents', 'properties'} or None, default None
        Fragment scope.
    """

    target: QueryTarget | Sequence[QueryTarget]
    query: StructuredQuery
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native container-query.

        Raises
        ------
        TypeError
            If a target is not an Element, JsonProperty or Field.
            If a subquery is not a StructuredQuery or is a Query wrapper.
            If a container target is not an Element or JsonProperty.
        ValueError
            If the targets are missing or of mixed kinds.
            If the fragment scope is not documents or properties.
        """
        _check_targets(self.target)
        _check_scope(self.fragment_scope)
        _check_subqueries(self.query)
        if any(
            not isinstance(target, (Element, JsonProperty))
            for target in _sequence(self.target)
        ):
            message = "Container queries require element or JSON property targets."
            raise TypeError(message)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native container-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native container-query.
        """
        targets = _targets(self.target, output_format=output_format)
        return _node(
            "container-query",
            targets
            + _scope(self.fragment_scope, output_format=output_format)
            + _subqueries(self.query, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class WordQuery(StructuredQuery):
    """Match terms or phrases at the selected location.

    Parameters
    ----------
    target : QueryTarget or Sequence[QueryTarget]
        Element, JSON property, or field descriptors.
    text : str or Sequence[str]
        Values or terms to match.
    attribute : Attribute or Sequence[Attribute] or None, default None
        Optional attributes of XML element targets.
    options : str or Sequence[str], optional
        Native term options.
    weight : float or None, default None
        Contribution to the relevance score.
    fragment_scope : {'documents', 'properties'} or None, default None
        Fragment scope.
    """

    target: QueryTarget | Sequence[QueryTarget]
    text: str | Sequence[str]
    attribute: Attribute | Sequence[Attribute] | None = None
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native word-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a target is not an Element, JsonProperty or Field.
        ValueError
            If the targets are missing or of mixed kinds, or attributes
            accompany non-Element targets.
            If the fragment scope is not documents or properties.
        """
        _check_types(self, "text", str)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_targets(self.target, self.attribute)
        _check_scope(self.fragment_scope)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native word-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native word-query.
        """
        return _node(
            "word-query",
            _targets(self.target, self.attribute, output_format=output_format)
            + _scope(self.fragment_scope, output_format=output_format)
            + _children("text", self.text, json_array=True, output_format=output_format)
            + _children(
                "term-option",
                self.options,
                json_array=True,
                output_format=output_format,
            )
            + _optional_children(weight=self.weight, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class ValueQuery(StructuredQuery):
    """Match whole values at the selected location.

    Parameters
    ----------
    target : QueryTarget or Sequence[QueryTarget]
        Element, JSON property, or field descriptors.
    text : str, int, float, bool, Decimal, date, datetime or Sequence
        Values to match. Use an empty string with node_type='null'.
    attribute : Attribute or Sequence[Attribute] or None, default None
        Optional attributes of XML element targets.
    options : str or Sequence[str], optional
        Native term options.
    weight : float or None, default None
        Contribution to the relevance score.
    fragment_scope : {'documents', 'properties'} or None, default None
        Fragment scope.
    node_type : {'string', 'boolean', 'null', 'number'} or None, default None
        JSON node type. Required to match non-string JSON values.
    """

    _VALUE_FIELDS: ClassVar[frozenset[str]] = frozenset({"text"})

    target: QueryTarget | Sequence[QueryTarget]
    text: _Scalar | Sequence[_Scalar]
    attribute: Attribute | Sequence[Attribute] | None = None
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None
    node_type: Literal["string", "boolean", "null", "number"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native value-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a target is not an Element, JsonProperty or Field.
        ValueError
            If the targets are missing or of mixed kinds, or attributes
            accompany non-Element targets.
            If the fragment scope is not documents or properties.
            If the JSON node type is unsupported.
        """
        _check_types(self, "text", _SCALAR_TYPES)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_targets(self.target, self.attribute)
        _check_scope(self.fragment_scope)
        if self.node_type not in (None, "string", "boolean", "null", "number"):
            message = "JSON node type must be string, boolean, null, or number."
            raise ValueError(message)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native value-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native value-query.
        """
        return _node(
            "value-query",
            _targets(self.target, self.attribute, output_format=output_format)
            + _scope(self.fragment_scope, output_format=output_format)
            + _children("text", self.text, json_array=True, output_format=output_format)
            + _children(
                "term-option",
                self.options,
                json_array=True,
                output_format=output_format,
            )
            + _optional_children(weight=self.weight, output_format=output_format),
            attributes={} if self.node_type is None else {"type": self.node_type},
            output_format=output_format,
        )


@dataclass(frozen=True)
class RangeQuery(StructuredQuery):
    """Compare typed values using a configured range index.

    Parameters
    ----------
    target : QueryTarget or Sequence[QueryTarget]
        Element, JSON property, or field descriptor.
        Range queries also accept PathIndex.
    value : str, int, float, bool, Decimal, date, datetime or Sequence
        One or more comparison values, serialized using XML lexical forms.
        Multiple values are supported only with EQ or NE.
    operator : {'LT', 'LE', 'GT', 'GE', 'EQ', 'NE'} or None, default None
        Comparison operator. The server default is EQ.
    index_type : str or None, default None
        Index type, for example xs:int.
    collation : str or None, default None
        String index collation URI.
    attribute : Attribute or Sequence[Attribute] or None, default None
        Optional attributes of XML element targets.
    options : str or Sequence[str], optional
        Native range query options.
    weight : float or None, default None
        Contribution to the relevance score.
    fragment_scope : {'documents', 'properties'} or None, default None
        Fragment scope.
    """

    _VALUE_FIELDS: ClassVar[frozenset[str]] = frozenset({"value"})

    target: QueryTarget | Sequence[QueryTarget]
    value: _Scalar | Sequence[_Scalar]
    operator: Literal["LT", "LE", "GT", "GE", "EQ", "NE"] | None = None
    index_type: str | None = None
    collation: str | None = None
    attribute: Attribute | Sequence[Attribute] | None = None
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native range-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a target is not an Element, JsonProperty or Field, or a
            PathIndex for a range.
        ValueError
            If the range operator is unsupported or the values do not suit it.
            If the targets are missing or of mixed kinds.
            If the fragment scope is not documents or properties.
        """
        _check_type(self, "index_type", str, optional=True)
        _check_type(self, "collation", str, optional=True)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_range_values(self.value, self.operator)
        _check_targets(self.target, self.attribute, allow_path=True)
        _check_scope(self.fragment_scope)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native range-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native range-query.
        """
        values = _sequence(self.value)
        attributes = {}
        if self.index_type is not None:
            attributes["type"] = self.index_type
        if self.collation is not None:
            attributes["collation"] = self.collation
        return _node(
            "range-query",
            _targets(
                self.target,
                self.attribute,
                output_format=output_format,
            )
            + _scope(self.fragment_scope, output_format=output_format)
            + _children("value", values, output_format=output_format)
            + _optional_children(
                range_operator=self.operator,
                output_format=output_format,
            )
            + _children("range-option", self.options, output_format=output_format)
            + _optional_children(weight=self.weight, output_format=output_format),
            attributes=attributes,
            output_format=output_format,
        )


@dataclass(frozen=True)
class CollectionConstraintQuery(StructuredQuery):
    """Build a collection-constraint-query using configured Search API options.

    Parameters
    ----------
    constraint_name : str
        Configured collection constraint name.
    uris : str or Sequence[str], default ()
        Collection suffixes appended to the configured prefix.
    """

    constraint_name: str
    uris: str | Sequence[str] = ()

    def _validate(self):
        """Reject arguments that cannot form a native collection-constraint-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        ValueError
            If the constraint name is missing or is not a single string.
        """
        _check_types(self, "uris", str)
        _check_constraint_name(self.constraint_name)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native collection-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native collection-constraint-query.
        """
        return _node(
            "collection-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _children("uri", self.uris, json_array=True, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class ContainerConstraintQuery(StructuredQuery):
    """Build a container-constraint-query using configured Search API options.

    Parameters
    ----------
    constraint_name : str
        Configured constraint name; combine separate queries with OrQuery.
    query : StructuredQuery
        Nested query applied within the configured containers.
    """

    constraint_name: str
    query: StructuredQuery

    def _validate(self):
        """Reject arguments that cannot form a native container-constraint-query.

        Raises
        ------
        TypeError
            If a subquery is not a StructuredQuery or is a Query wrapper.
        ValueError
            If the constraint name is missing or is not a single string.
        """
        _check_constraint_name(self.constraint_name)
        _check_subqueries(self.query)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native container-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native container-constraint-query.
        """
        return _node(
            "container-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _subqueries(self.query, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class ElementConstraintQuery(StructuredQuery):
    """Build a legacy element constraint; prefer ContainerConstraintQuery.

    Parameters
    ----------
    constraint_name : str
        Configured constraint name; combine separate queries with OrQuery.
    query : StructuredQuery
        Nested query.
    """

    constraint_name: str
    query: StructuredQuery

    def _validate(self):
        """Reject arguments that cannot form a native element-constraint-query.

        Raises
        ------
        TypeError
            If a subquery is not a StructuredQuery or is a Query wrapper.
        ValueError
            If the constraint name is missing or is not a single string.
        """
        _check_constraint_name(self.constraint_name)
        _check_subqueries(self.query)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native element-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native element-constraint-query.
        """
        return _node(
            "element-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _subqueries(self.query, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class PropertiesConstraintQuery(StructuredQuery):
    """Build a properties-constraint-query using configured Search API options.

    Parameters
    ----------
    constraint_name : str
        Configured properties constraint name.
    query : StructuredQuery
        Query applied to document properties.
    """

    constraint_name: str
    query: StructuredQuery

    def _validate(self):
        """Reject arguments that cannot form a native properties-constraint-query.

        Raises
        ------
        TypeError
            If a subquery is not a StructuredQuery or is a Query wrapper.
        ValueError
            If the constraint name is missing or is not a single string.
        """
        _check_constraint_name(self.constraint_name)
        _check_subqueries(self.query)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native properties-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native properties-constraint-query.
        """
        return _node(
            "properties-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _subqueries(self.query, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class CustomConstraintQuery(StructuredQuery):
    """Build a custom-constraint-query using configured Search API options.

    Parameters
    ----------
    constraint_name : str
        Configured custom constraint name.
    text : str or Sequence[str], default ()
        Values passed to the configured custom parser.
    """

    constraint_name: str
    text: str | Sequence[str] = ()

    def _validate(self):
        """Reject arguments that cannot form a native custom-constraint-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        ValueError
            If the constraint name is missing or is not a single string.
        """
        _check_types(self, "text", str)
        _check_constraint_name(self.constraint_name)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native custom-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native custom-constraint-query.
        """
        return _node(
            "custom-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _children(
                "text",
                self.text,
                json_array=True,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class WordConstraintQuery(StructuredQuery):
    """Build a word-constraint-query using configured Search API options.

    Parameters
    ----------
    constraint_name : str
        Configured constraint name; combine separate queries with OrQuery.
    text : str or Sequence[str], default ()
        Words to match.
    weight : float or None, default None
        Optional query weight.
    """

    constraint_name: str
    text: str | Sequence[str] = ()
    weight: float | None = None

    def _validate(self):
        """Reject arguments that cannot form a native word-constraint-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        ValueError
            If the constraint name is missing or is not a single string.
        """
        _check_types(self, "text", str)
        _check_number(self, "weight", optional=True)
        _check_constraint_name(self.constraint_name)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native word-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native word-constraint-query.
        """
        return _node(
            "word-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _children("text", self.text, json_array=True, output_format=output_format)
            + _optional_children(weight=self.weight, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class OperatorState(StructuredQuery):
    """Select an operator state using configured Search API options.

    Parameters
    ----------
    operator_name : str
        Operator configured in Search API options.
    state_name : str
        Named state selecting the operator options.
    """

    operator_name: str
    state_name: str

    def _validate(self):
        """Reject arguments that cannot form a native operator-state.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_type(self, "operator_name", str)
        _check_type(self, "state_name", str)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native operator-state in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native operator-state.
        """
        return _as_json_array(
            _node(
                "operator-state",
                _children(
                    "operator-name",
                    self.operator_name,
                    output_format=output_format,
                )
                + _children("state-name", self.state_name, output_format=output_format),
                output_format=output_format,
            ),
        )


@dataclass(frozen=True)
class RangeConstraintQuery(StructuredQuery):
    """Build a range-constraint-query using configured Search API options.

    Parameters
    ----------
    constraint_name : str
        Configured range constraint name.
    value : str, int, float, bool, Decimal, date, datetime or Sequence
        Values cast using the configured range index type.
    operator : {'LT', 'LE', 'GT', 'GE', 'EQ', 'NE'} or None, default None
        Range comparison; multiple values require EQ or NE.
    options : str or Sequence[str], default ()
        Range query options.
    """

    _VALUE_FIELDS: ClassVar[frozenset[str]] = frozenset({"value"})

    constraint_name: str
    value: _Scalar | Sequence[_Scalar]
    operator: Literal["LT", "LE", "GT", "GE", "EQ", "NE"] | None = None
    options: str | Sequence[str] = ()

    def _validate(self):
        """Reject arguments that cannot form a native range-constraint-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        ValueError
            If the constraint name is missing or is not a single string.
            If the range operator is unsupported or the values do not suit it.
        """
        _check_types(self, "options", str)
        _check_constraint_name(self.constraint_name)
        _check_range_values(self.value, self.operator)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native range-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native range-constraint-query.
        """
        return _node(
            "range-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _children(
                "value",
                _sequence(self.value),
                output_format=output_format,
            )
            + _optional_children(
                range_operator=self.operator,
                output_format=output_format,
            )
            + _children("range-option", self.options, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class ValueConstraintQuery(StructuredQuery):
    """Build a value-constraint-query using configured Search API options.

    Parameters
    ----------
    constraint_name : str
        Configured value constraint name.
    text : str, int, float, bool, Decimal, date, datetime or Sequence, default ()
        Values serialized as text; JSON types come from constraint options.
    weight : float or None, default None
        Optional query weight.
    """

    _VALUE_FIELDS: ClassVar[frozenset[str]] = frozenset({"text"})

    constraint_name: str
    text: _Scalar | Sequence[_Scalar] = ()
    weight: float | None = None

    def _validate(self):
        """Reject arguments that cannot form a native value-constraint-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        ValueError
            If the constraint name is missing or is not a single string.
        """
        _check_types(self, "text", _SCALAR_TYPES)
        _check_number(self, "weight", optional=True)
        _check_constraint_name(self.constraint_name)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native value-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native value-constraint-query.
        """
        return _node(
            "value-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _children("text", self.text, json_array=True, output_format=output_format)
            + _optional_children(weight=self.weight, output_format=output_format),
            output_format=output_format,
        )


class Region(QueryComponent, _Validated):
    """Represent geographic criteria in structured queries."""


@dataclass(frozen=True)
class Point(Region):
    """Build Search API point criteria.

    Parameters
    ----------
    latitude : float
        Latitude in the selected coordinate system.
    longitude : float
        Longitude in the selected coordinate system.
    """

    latitude: float
    longitude: float

    def _validate(self):
        """Reject arguments that cannot form a native point.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_number(self, "latitude")
        _check_number(self, "longitude")

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native point in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native point.
        """
        return _as_json_array(
            _node(
                "point",
                _optional_children(
                    latitude=self.latitude,
                    longitude=self.longitude,
                    output_format=output_format,
                ),
                output_format=output_format,
            ),
        )


@dataclass(frozen=True)
class Box(Region):
    """Build Search API box criteria.

    Parameters
    ----------
    south : float
        Southern boundary.
    west : float
        Western boundary.
    north : float
        Northern boundary.
    east : float
        Eastern boundary.
    """

    south: float
    west: float
    north: float
    east: float

    def _validate(self):
        """Reject arguments that cannot form a native box.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_number(self, "south")
        _check_number(self, "west")
        _check_number(self, "north")
        _check_number(self, "east")

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native box in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native box.
        """
        return _as_json_array(
            _node(
                "box",
                _optional_children(
                    south=self.south,
                    west=self.west,
                    north=self.north,
                    east=self.east,
                    output_format=output_format,
                ),
                output_format=output_format,
            ),
        )


@dataclass(frozen=True)
class Circle(Region):
    """Build Search API circle criteria.

    Parameters
    ----------
    radius : float
        Radius in units selected by the query options.
    center : Point
        Circle center.
    """

    radius: float
    center: Point

    def _validate(self):
        """Reject arguments that cannot form a native circle.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_number(self, "radius")
        _check_type(self, "center", Point)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native circle in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native circle.
        """
        return _as_json_array(
            _node(
                "circle",
                [
                    *_optional_children(
                        radius=self.radius,
                        output_format=output_format,
                    ),
                    self.center.serialize(output_format),
                ],
                output_format=output_format,
            ),
        )


@dataclass(frozen=True)
class Polygon(Region):
    """Build Search API polygon criteria.

    Parameters
    ----------
    points : Sequence[Point]
        Ordered polygon vertices.
    """

    points: Sequence[Point]

    def _validate(self):
        """Reject arguments that cannot form a native polygon.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_types(self, "points", Point)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native polygon in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native polygon.
        """
        return _as_json_array(
            _node(
                "polygon",
                [point.serialize(output_format) for point in self.points],
                output_format=output_format,
            ),
        )


@dataclass(frozen=True)
class Period(QueryComponent, _Validated):
    """Build Search API period criteria.

    Parameters
    ----------
    start : datetime or str
        Inclusive start instant.
    end : datetime or str
        Exclusive end instant.
    """

    start: datetime | str
    end: datetime | str

    def _validate(self):
        """Reject arguments that cannot form a native period.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_type(self, "start", (datetime, str))
        _check_type(self, "end", (datetime, str))

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native period in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native period.
        """
        return _as_json_array(
            _node(
                "period",
                _optional_children(
                    period_start=self.start,
                    period_end=self.end,
                    output_format=output_format,
                ),
                output_format=output_format,
            ),
        )


@dataclass(frozen=True)
class GeoElementQuery(StructuredQuery):
    """Build Search API geo-elem-query criteria.

    Parameters
    ----------
    element : Element
        Indexed element containing point data.
    regions : Region or Sequence[Region]
        Geographic criteria.
    parent : Element or None, default None
        Optional parent identifying a child element index.
    options : str or Sequence[str], default ()
        Native geospatial query options.
    weight : float or None, default None
        Optional query weight.
    fragment_scope : {'documents', 'properties'} or None, default None
        Optional documents or properties fragment scope.
    """

    element: Element
    regions: Region | Sequence[Region]
    parent: Element | None = None
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native geo-elem-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a geospatial criterion is not a Region.
        ValueError
            If the fragment scope is not documents or properties.
        """
        _check_type(self, "element", Element)
        _check_type(self, "parent", Element, optional=True)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_regions(self.regions)
        _check_scope(self.fragment_scope)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native geo-elem-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native geo-elem-query.
        """
        return _node(
            "geo-elem-query",
            _geo_target("parent", self.parent, output_format=output_format)
            + _geo_target("element", self.element, output_format=output_format)
            + _geo_children(
                self.regions,
                self.options,
                self.weight,
                self.fragment_scope,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class GeoElementPairQuery(StructuredQuery):
    """Build Search API geo-elem-pair-query criteria.

    Parameters
    ----------
    parent : Element
        Containing element.
    latitude : Element
        Latitude element.
    longitude : Element
        Longitude element.
    regions : Region or Sequence[Region]
        Point, box, circle, or polygon criteria; combined with OR.
    options : str or Sequence[str], default ()
        Native geospatial query options.
    weight : float or None, default None
        Optional query weight.
    fragment_scope : {'documents', 'properties'} or None, default None
        Optional documents or properties fragment scope.
    """

    parent: Element
    latitude: Element
    longitude: Element
    regions: Region | Sequence[Region]
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native geo-elem-pair-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a geospatial criterion is not a Region.
        ValueError
            If the fragment scope is not documents or properties.
        """
        _check_type(self, "parent", Element)
        _check_type(self, "latitude", Element)
        _check_type(self, "longitude", Element)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_regions(self.regions)
        _check_scope(self.fragment_scope)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native geo-elem-pair-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native geo-elem-pair-query.
        """
        return _node(
            "geo-elem-pair-query",
            _geo_target("parent", self.parent, output_format=output_format)
            + _geo_target("lat", self.latitude, output_format=output_format)
            + _geo_target("lon", self.longitude, output_format=output_format)
            + _geo_children(
                self.regions,
                self.options,
                self.weight,
                self.fragment_scope,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class GeoAttributePairQuery(StructuredQuery):
    """Build Search API geo-attr-pair-query criteria.

    Parameters
    ----------
    parent : Element
        Containing element.
    latitude : Attribute
        Latitude attribute.
    longitude : Attribute
        Longitude attribute.
    regions : Region or Sequence[Region]
        Point, box, circle, or polygon criteria; combined with OR.
    options : str or Sequence[str], default ()
        Native geospatial query options.
    weight : float or None, default None
        Optional query weight.
    fragment_scope : {'documents', 'properties'} or None, default None
        Optional documents or properties fragment scope.
    """

    parent: Element
    latitude: Attribute
    longitude: Attribute
    regions: Region | Sequence[Region]
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native geo-attr-pair-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a geospatial criterion is not a Region.
        ValueError
            If the fragment scope is not documents or properties.
        """
        _check_type(self, "parent", Element)
        _check_type(self, "latitude", Attribute)
        _check_type(self, "longitude", Attribute)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_regions(self.regions)
        _check_scope(self.fragment_scope)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native geo-attr-pair-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native geo-attr-pair-query.
        """
        return _node(
            "geo-attr-pair-query",
            _geo_target("parent", self.parent, output_format=output_format)
            + _geo_target("lat", self.latitude, output_format=output_format)
            + _geo_target("lon", self.longitude, output_format=output_format)
            + _geo_children(
                self.regions,
                self.options,
                self.weight,
                self.fragment_scope,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class GeoPathQuery(StructuredQuery):
    """Build Search API geo-path-query criteria.

    Parameters
    ----------
    path : PathIndex
        Indexed path and namespace bindings.
    regions : Region or Sequence[Region]
        Point, box, circle, or polygon criteria; combined with OR.
    options : str or Sequence[str], default ()
        Native geospatial query options.
    weight : float or None, default None
        Optional query weight.
    fragment_scope : {'documents', 'properties'} or None, default None
        Optional documents or properties fragment scope.
    """

    path: PathIndex
    regions: Region | Sequence[Region]
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native geo-path-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a geospatial criterion is not a Region.
        ValueError
            If the fragment scope is not documents or properties.
        """
        _check_type(self, "path", PathIndex)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_regions(self.regions)
        _check_scope(self.fragment_scope)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native geo-path-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native geo-path-query.
        """
        return _node(
            "geo-path-query",
            [
                self.path.serialize(output_format),
                *_geo_children(
                    self.regions,
                    self.options,
                    self.weight,
                    self.fragment_scope,
                    output_format=output_format,
                ),
            ],
            output_format=output_format,
        )


@dataclass(frozen=True)
class GeoJsonPropertyQuery(StructuredQuery):
    """Build Search API geo-json-property-query criteria.

    Parameters
    ----------
    property : JsonProperty
        Indexed property containing point data.
    regions : Region or Sequence[Region]
        Geographic criteria.
    parent : JsonProperty or None, default None
        Optional containing property for a child index.
    options : str or Sequence[str], default ()
        Native geospatial query options.
    weight : float or None, default None
        Optional query weight.
    fragment_scope : {'documents', 'properties'} or None, default None
        Optional documents or properties fragment scope.
    """

    property: JsonProperty
    regions: Region | Sequence[Region]
    parent: JsonProperty | None = None
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native geo-json-property-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a JSON property selector is not a JsonProperty.
            If a geospatial criterion is not a Region.
        ValueError
            If the fragment scope is not documents or properties.
        """
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_json_properties(self.property, self.parent)
        _check_regions(self.regions)
        _check_scope(self.fragment_scope)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native geo-json-property-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native geo-json-property-query.
        """
        return _node(
            "geo-json-property-query",
            _optional_children(
                parent_property=None if self.parent is None else self.parent.name,
                output_format=output_format,
            )
            + _children(
                "json-property",
                self.property.name,
                output_format=output_format,
            )
            + _geo_children(
                self.regions,
                self.options,
                self.weight,
                self.fragment_scope,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class GeoJsonPropertyPairQuery(StructuredQuery):
    """Build Search API geo-json-property-pair-query criteria.

    Parameters
    ----------
    parent : JsonProperty
        Containing property.
    latitude : JsonProperty
        Latitude property.
    longitude : JsonProperty
        Longitude property.
    regions : Region or Sequence[Region]
        Point, box, circle, or polygon criteria; combined with OR.
    options : str or Sequence[str], default ()
        Native geospatial query options.
    weight : float or None, default None
        Optional query weight.
    fragment_scope : {'documents', 'properties'} or None, default None
        Optional documents or properties fragment scope.
    """

    parent: JsonProperty
    latitude: JsonProperty
    longitude: JsonProperty
    regions: Region | Sequence[Region]
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native geo-json-property-pair-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a JSON property selector is not a JsonProperty.
            If a geospatial criterion is not a Region.
        ValueError
            If the fragment scope is not documents or properties.
        """
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_json_properties(self.parent, self.latitude, self.longitude)
        _check_regions(self.regions)
        _check_scope(self.fragment_scope)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native geo-json-property-pair-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native geo-json-property-pair-query.
        """
        return _node(
            "geo-json-property-pair-query",
            _children(
                "parent-property",
                self.parent.name,
                output_format=output_format,
            )
            + _children(
                "lat-property",
                self.latitude.name,
                output_format=output_format,
            )
            + _children(
                "lon-property",
                self.longitude.name,
                output_format=output_format,
            )
            + _geo_children(
                self.regions,
                self.options,
                self.weight,
                self.fragment_scope,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class GeoRegionPathQuery(StructuredQuery):
    """Build Search API geo-region-path-query criteria.

    Parameters
    ----------
    path : PathIndex
        Indexed region path and namespace bindings.
    regions : Region or Sequence[Region]
        Geographic criteria.
    operator : str or None, default None
        Optional topological relationship, e.g. intersects.
    coord : str or None, default None
        Coordinate system identifying the region index.
    options : str or Sequence[str], default ()
        Native geospatial query options.
    weight : float or None, default None
        Query weight, serialized as given; MarkLogic 12.1 does not apply it
        to the resolved geospatial-region-query.
    fragment_scope : {'documents', 'properties'} or None, default None
        Optional documents or properties fragment scope.
    """

    path: PathIndex
    regions: Region | Sequence[Region]
    operator: _GeospatialOperator | None = None
    coord: str | None = None
    options: str | Sequence[str] = ()
    weight: float | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def _validate(self):
        """Reject arguments that cannot form a native geo-region-path-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a geospatial criterion is not a Region.
        ValueError
            If the operator is not a native geospatial operator.
            If the fragment scope is not documents or properties.
        """
        _check_type(self, "path", PathIndex)
        _check_choice(
            self,
            "operator",
            _GEOSPATIAL_OPERATORS,
            "geospatial operator",
            optional=True,
        )
        _check_type(self, "coord", str, optional=True)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)
        _check_regions(self.regions)
        _check_scope(self.fragment_scope)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native geo-region-path-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native geo-region-path-query.
        """
        return _node(
            "geo-region-path-query",
            [
                self.path.serialize(output_format),
                *_optional_children(
                    geospatial_operator=self.operator,
                    output_format=output_format,
                ),
                *_geo_children(
                    self.regions,
                    self.options,
                    self.weight,
                    self.fragment_scope,
                    output_format=output_format,
                ),
            ],
            attributes={"coord": self.coord} if self.coord is not None else {},
            output_format=output_format,
        )


@dataclass(frozen=True)
class GeospatialConstraintQuery(StructuredQuery):
    """Build Search API geospatial-constraint-query criteria.

    Parameters
    ----------
    constraint_name : str
        Configured geospatial constraint name.
    regions : Region or Sequence[Region]
        Geographic criteria.
    text : str or Sequence[str], default ()
        Optional string criteria interpreted by the constraint.
    """

    constraint_name: str
    regions: Region | Sequence[Region]
    text: str | Sequence[str] = ()

    def _validate(self):
        """Reject arguments that cannot form a native geospatial-constraint-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a geospatial criterion is not a Region.
        ValueError
            If the constraint name is missing or is not a single string.
        """
        _check_types(self, "text", str)
        _check_constraint_name(self.constraint_name)
        _check_regions(self.regions)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native geospatial-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native geospatial-constraint-query.
        """
        return _node(
            "geospatial-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _regions(self.regions, output_format=output_format)
            + _children(
                "text",
                self.text,
                json_array=True,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class GeoRegionConstraintQuery(StructuredQuery):
    """Build Search API geo-region-constraint-query criteria.

    Parameters
    ----------
    constraint_name : str
        Configured geospatial region constraint.
    regions : Region or Sequence[Region]
        Geographic criteria.
    operator : str or None, default None
        Optional topological relationship.
    weight : float or None, default None
        Query weight, serialized as given; MarkLogic 12.1 does not apply it
        to the resolved geospatial-region-query.
    """

    constraint_name: str
    regions: Region | Sequence[Region]
    operator: _GeospatialOperator | None = None
    weight: float | None = None

    def _validate(self):
        """Reject arguments that cannot form a native geo-region-constraint-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
            If a geospatial criterion is not a Region.
        ValueError
            If the operator is not a native geospatial operator.
            If the constraint name is missing or is not a single string.
        """
        _check_choice(
            self,
            "operator",
            _GEOSPATIAL_OPERATORS,
            "geospatial operator",
            optional=True,
        )
        _check_number(self, "weight", optional=True)
        _check_constraint_name(self.constraint_name)
        _check_regions(self.regions)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native geo-region-constraint-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native geo-region-constraint-query.
        """
        return _node(
            "geo-region-constraint-query",
            _constraint_name(self.constraint_name, output_format=output_format)
            + _optional_children(
                geospatial_operator=self.operator,
                output_format=output_format,
            )
            + _regions(self.regions, output_format=output_format)
            + _optional_children(weight=self.weight, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class LsqtQuery(StructuredQuery):
    """Build Search API lsqt-query criteria.

    Parameters
    ----------
    temporal_collection : str
        Configured temporal collection.
    timestamp : datetime or str or None, default None
        Optional timestamp at or before LSQT.
    options : str or Sequence[str], default ()
        Native temporal query options.
    weight : float or None, default None
        Optional query weight.
    """

    temporal_collection: str
    timestamp: datetime | str | None = None
    options: str | Sequence[str] = ()
    weight: float | None = None

    def _validate(self):
        """Reject arguments that cannot form a native lsqt-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_type(self, "temporal_collection", str)
        _check_type(self, "timestamp", (datetime, str), optional=True)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native lsqt-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native lsqt-query.
        """
        return _node(
            "lsqt-query",
            _children(
                "temporal-collection",
                self.temporal_collection,
                output_format=output_format,
            )
            + _optional_children(
                timestamp=self.timestamp,
                weight=self.weight,
                output_format=output_format,
            )
            + _children(
                "temporal-option",
                self.options,
                json_array=True,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class PeriodCompareQuery(StructuredQuery):
    """Build Search API period-compare-query criteria.

    Parameters
    ----------
    axis1 : str
        First temporal axis.
    operator : str
        Native temporal comparison operator.
    axis2 : str
        Second temporal axis.
    options : str or Sequence[str], default ()
        Native temporal query options.
    """

    axis1: str
    operator: _TemporalOperator
    axis2: str
    options: str | Sequence[str] = ()

    def _validate(self):
        """Reject arguments that cannot form a native period-compare-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        ValueError
            If the operator is not a native temporal operator.
        """
        _check_type(self, "axis1", str)
        _check_choice(self, "operator", _TEMPORAL_OPERATORS, "temporal operator")
        _check_type(self, "axis2", str)
        _check_types(self, "options", str)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native period-compare-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native period-compare-query.
        """
        return _node(
            "period-compare-query",
            _children("axis1", self.axis1, output_format=output_format)
            + _children("temporal-operator", self.operator, output_format=output_format)
            + _children("axis2", self.axis2, output_format=output_format)
            + _children(
                "temporal-option",
                self.options,
                json_array=True,
                output_format=output_format,
            ),
            output_format=output_format,
        )


@dataclass(frozen=True)
class PeriodRangeQuery(StructuredQuery):
    """Build Search API period-range-query criteria.

    Parameters
    ----------
    axes : str or Sequence[str]
        Temporal axes.
    operator : str
        Native temporal comparison operator.
    periods : Period or Sequence[Period]
        Periods compared with the indexed axes.
    options : str or Sequence[str], default ()
        Native temporal query options.
    weight : float or None, default None
        Optional query weight.
    """

    axes: str | Sequence[str]
    operator: _TemporalOperator
    periods: Period | Sequence[Period]
    options: str | Sequence[str] = ()
    weight: float | None = None

    def _validate(self):
        """Reject arguments that cannot form a native period-range-query.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        ValueError
            If the operator is not a native temporal operator.
        """
        _check_types(self, "axes", str)
        _check_choice(self, "operator", _TEMPORAL_OPERATORS, "temporal operator")
        _check_types(self, "periods", Period)
        _check_types(self, "options", str)
        _check_number(self, "weight", optional=True)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native period-range-query in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native period-range-query.
        """
        return _node(
            "period-range-query",
            _children("axis", self.axes, json_array=True, output_format=output_format)
            + _children("temporal-operator", self.operator, output_format=output_format)
            + [period.serialize(output_format) for period in _sequence(self.periods)]
            + _children(
                "temporal-option",
                self.options,
                json_array=True,
                output_format=output_format,
            )
            + _optional_children(weight=self.weight, output_format=output_format),
            output_format=output_format,
        )


@dataclass(frozen=True)
class QtextQuery(StructuredQuery):
    """Build Search API qtext criteria.

    Parameters
    ----------
    text : str
        String query interpreted using Search API options.
    """

    text: str

    def _validate(self):
        """Reject arguments that cannot form a native qtext.

        Raises
        ------
        TypeError
            If an argument has an unsupported type.
        """
        _check_type(self, "text", str)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the native qtext in the requested format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native qtext.
        """
        return _as_json_array(
            _node("qtext", text=self.text, output_format=output_format),
        )


class StructuredQueryBuilder:
    """Build composable queries without executing them or storing mutable state.

    Leaf factories use the signatures of their corresponding query classes.
    Composer factories accept positional subqueries, like the Java builder.
    All returned queries support serialize() for JSON and serialize("xml") for XML.
    """

    def query(self, *queries: StructuredQuery) -> Query:
        """Wrap structured queries for submission to the Search API.

        Parameters
        ----------
        *queries : StructuredQuery
            Top-level query components.

        Returns
        -------
        Query
            Structured-query wrapper.
        """
        return Query(queries)

    def and_(
        self,
        *queries: StructuredQuery,
        ordered: bool | None = None,
    ) -> AndQuery:
        """Build the intersection of positional query components.

        Parameters
        ----------
        *queries : StructuredQuery
            Queries that must all match.
        ordered : bool or None, default None
            Optional position-order requirement.

        Returns
        -------
        AndQuery
            Composable intersection query.
        """
        return AndQuery(queries, ordered=ordered)

    def or_(self, *queries: StructuredQuery) -> OrQuery:
        """Build the union of positional query components.

        Parameters
        ----------
        *queries : StructuredQuery
            Alternative queries.

        Returns
        -------
        OrQuery
            Composable union query.
        """
        return OrQuery(queries)

    def near(
        self,
        *queries: StructuredQuery,
        distance: int | None = None,
        minimum_distance: int | None = None,
        distance_weight: float | None = None,
        ordered: bool | None = None,
    ) -> NearQuery:
        """Build proximity criteria for positional query components.

        Parameters
        ----------
        *queries : StructuredQuery
            Queries whose matches must be near each other.
        distance : int or None, default None
            Maximum distance.
        minimum_distance : int or None, default None
            Minimum distance.
        distance_weight : float or None, default None
            Distance scoring weight.
        ordered : bool or None, default None
            Optional match order.

        Returns
        -------
        NearQuery
            Composable proximity query.
        """
        return NearQuery(
            queries,
            distance=distance,
            minimum_distance=minimum_distance,
            distance_weight=distance_weight,
            ordered=ordered,
        )

    and_not = AndNotQuery
    attribute = Attribute
    boost = BoostQuery
    box = Box
    circle = Circle
    collection_constraint = CollectionConstraintQuery
    collection = CollectionQuery
    container_constraint = ContainerConstraintQuery
    container = ContainerQuery
    custom_constraint = CustomConstraintQuery
    directory = DirectoryQuery
    document_fragment = DocumentFragmentQuery
    document = DocumentQuery
    element = Element
    element_constraint = ElementConstraintQuery
    false = FalseQuery
    field = Field
    geo_attribute_pair = GeoAttributePairQuery
    geo_element_pair = GeoElementPairQuery
    geo_element = GeoElementQuery
    geo_json_property_pair = GeoJsonPropertyPairQuery
    geo_json_property = GeoJsonPropertyQuery
    geo_path = GeoPathQuery
    geo_region_constraint = GeoRegionConstraintQuery
    geo_region_path = GeoRegionPathQuery
    geospatial_constraint = GeospatialConstraintQuery
    json_property = JsonProperty
    locks_fragment = LocksFragmentQuery
    lsqt = LsqtQuery
    not_in = NotInQuery
    not_ = NotQuery
    operator_state = OperatorState
    path_index = PathIndex
    period = Period
    period_compare = PeriodCompareQuery
    period_range = PeriodRangeQuery
    point = Point
    polygon = Polygon
    properties_constraint = PropertiesConstraintQuery
    properties_fragment = PropertiesFragmentQuery
    qtext = QtextQuery
    range_constraint = RangeConstraintQuery
    range = RangeQuery
    term = TermQuery
    true = TrueQuery
    value_constraint = ValueConstraintQuery
    value = ValueQuery
    word_constraint = WordConstraintQuery
    word = WordQuery


sq = StructuredQueryBuilder()
"""Stateless structured-query builder; equivalent to StructuredQueryBuilder()."""


def _queries_node(
    name: str,
    children: Sequence[XmlElement | dict],
    *,
    output_format: Literal["json", "xml"] = "xml",
) -> XmlElement | dict:
    """Build a composing query whose JSON holds its children in ``queries``.

    The native JSON grammar of query, and-query, or-query and near-query
    lists subqueries and options alike as members of one queries array.

    Parameters
    ----------
    name : str
        Native member name.
    children : Sequence[xml.etree.ElementTree.Element or dict]
        Subqueries and options in the selected representation.
    output_format : {'json', 'xml'}, default 'xml'
        Requested representation.

    Returns
    -------
    xml.etree.ElementTree.Element or dict
        Fresh native component.
    """
    if output_format == "json":
        return {name: {"queries": [_json_full_member(child) for child in children]}}
    return _node(name, children, output_format=output_format)


def _as_json_array(component: XmlElement | dict) -> XmlElement | dict:
    """Hold a JSON member's value in an array, as native JSON always does for it.

    Parameters
    ----------
    component : xml.etree.ElementTree.Element or dict
        One serialized component; XML is returned unchanged.

    Returns
    -------
    xml.etree.ElementTree.Element or dict
        The component, its JSON value wrapped in a one-item array.
    """
    if not isinstance(component, dict):
        return component
    ((name, value),) = component.items()
    return {name: [value]}


def _json_full_member(member: dict) -> dict:
    """Wrap a full-query array member using native scalar metadata conventions.

    Parameters
    ----------
    member : dict
        One named, directly serialized component.

    Returns
    -------
    dict
        Member suitable for a queries array.
    """
    name, value = next(iter(member.items()))
    # Standalone, qtext and operator-state are arrays; inside a queries array
    # the native grammar holds each one as a single member.
    if name in {"qtext", "operator-state"}:
        value = value[0]
    if value is not None and not isinstance(value, (dict, list)):
        value = {_TEXT_VALUE_KEY: value}
    return {name: value}


def _json_members(
    children: Sequence[dict],
    attributes: Mapping[str, str] | None,
) -> dict:
    """Combine direct JSON children without discarding repeated criteria.

    Parameters
    ----------
    children : Sequence[dict]
        Named child members.
    attributes : Mapping[str, str] or None
        Parent descriptor metadata.

    Returns
    -------
    dict
        Combined native component content.
    """
    result = dict(attributes or {})
    for child in children:
        for key, value in child.items():
            if key in result:
                previous = result[key]
                result[key] = (
                    [*previous, *(value if isinstance(value, list) else [value])]
                    if isinstance(previous, list)
                    else [previous, value]
                )
            else:
                result[key] = value
    return result


def _geo_target(
    name: str,
    target: Element | Attribute | None,
    *,
    output_format: Literal["json", "xml"] = "xml",
) -> list[XmlElement | dict]:
    """Serialize an optional geospatial element or attribute selector.

    Parameters
    ----------
    name : str
        Selector role: parent, element, lat, or lon.
    target : Element or Attribute or None
        XML name descriptor.
    output_format : {'json', 'xml'}, default 'xml'
        Requested serialization format.

    Returns
    -------
    list[xml.etree.ElementTree.Element or dict]
        Optional renamed selector.
    """
    if target is None:
        return []
    return [
        _node(
            name,
            attributes={"name": target.name, "ns": target.ns},
            output_format=output_format,
        ),
    ]


def _geo_children(
    regions: Region | Sequence[Region],
    options: str | Sequence[str],
    weight: float | None,
    fragment_scope: str | None,
    *,
    output_format: Literal["json", "xml"] = "xml",
) -> list[XmlElement | dict]:
    """Serialize shared geospatial criteria and options.

    Parameters
    ----------
    regions : Region or Sequence[Region]
        Geographic criteria.
    options : str or Sequence[str]
        Native geospatial options.
    weight : float or None
        Optional query weight.
    fragment_scope : str or None
        Optional fragment scope.
    output_format : {'json', 'xml'}, default 'xml'
        Requested serialization format.

    Returns
    -------
    list[xml.etree.ElementTree.Element or dict]
        Geographic criteria and options.
    """
    return (
        _children("geo-option", options, json_array=True, output_format=output_format)
        + _scope(fragment_scope, output_format=output_format)
        + _regions(regions, output_format=output_format)
        + _optional_children(weight=weight, output_format=output_format)
    )


def _regions(
    regions: Region | Sequence[Region],
    *,
    output_format: Literal["json", "xml"] = "xml",
) -> list[XmlElement | dict]:
    """Serialize geographic criteria, checked by _check_regions.

    Parameters
    ----------
    regions : Region or Sequence[Region]
        Point, box, circle, or polygon criteria.
    output_format : {'json', 'xml'}, default 'xml'
        Requested serialization format.

    Returns
    -------
    list[xml.etree.ElementTree.Element or dict]
        Search API region elements.
    """
    return [region.serialize(output_format) for region in _sequence(regions)]


def _check_regions(regions: Region | Sequence[Region]):
    """Reject geographic criteria that are not regions.

    Parameters
    ----------
    regions : Region or Sequence[Region]
        Point, box, circle, or polygon criteria.

    Raises
    ------
    TypeError
        If a criterion is not a Region instance.
    """
    if any(not isinstance(region, Region) for region in _sequence(regions)):
        message = "Geospatial criteria must be Region instances."
        raise TypeError(message)


def _constraint_name(
    name: str,
    *,
    output_format: Literal["json", "xml"] = "xml",
) -> list[XmlElement | dict]:
    """Serialize one constraint name, checked by _check_constraint_name.

    Parameters
    ----------
    name : str
        Non-empty constraint name.
    output_format : {'json', 'xml'}, default 'xml'
        Requested serialization format.

    Returns
    -------
    list[xml.etree.ElementTree.Element or dict]
        One constraint-name child.
    """
    return _children("constraint-name", name, output_format=output_format)


def _check_constraint_name(name: str):
    """Reject a missing constraint name or several names.

    Parameters
    ----------
    name : str
        Non-empty constraint name.

    Raises
    ------
    ValueError
        If the name is missing or is not a single string.
    """
    if not isinstance(name, str) or not name:
        message = "Use one non-empty constraint name; combine queries with OrQuery."
        raise ValueError(message)


def _check_range_values(
    value: _Scalar | Sequence[_Scalar],
    operator: str | None,
):
    """Reject a range comparison or value cardinality MarkLogic cannot evaluate.

    Parameters
    ----------
    value : Any or Sequence
        Range values.
    operator : str or None
        Search API comparison operator.

    Raises
    ------
    ValueError
        If the operator or value cardinality is invalid.
    """
    if operator not in (None, "LT", "LE", "GT", "GE", "EQ", "NE"):
        message = "Range operator must be LT, LE, GT, GE, EQ, or NE."
        raise ValueError(message)
    values = _sequence(value)
    if not values:
        message = "Range queries require at least one value."
        raise ValueError(message)
    if len(values) > 1 and operator not in (None, "EQ", "NE"):
        message = "Multiple range values require EQ or NE."
        raise ValueError(message)


def _node(
    name: str,
    children: Sequence[XmlElement | dict] = (),
    *,
    attributes: Mapping[str, str] | None = None,
    text: str | None = None,
    output_format: Literal["json", "xml"] = "xml",
) -> XmlElement | dict:
    """Build a Search API component with the selected independent serializer.

    Parameters
    ----------
    name : str
        Local element name.
    children : Sequence[xml.etree.ElementTree.Element or dict], optional
        Ordered children in the selected representation.
    attributes : Mapping[str, str] or None, default None
        XML attributes and optional namespace declarations.
    text : str or None, default None
        Literal text; XML escapes it during serialization.
    output_format : {'json', 'xml'}, default 'xml'
        Requested representation.

    Returns
    -------
    xml.etree.ElementTree.Element or dict
        Fresh native component containing the supplied children.
    """
    if output_format == "json":
        return _json_node(name, children, attributes=attributes, text=text)
    return _xml_node(name, children, attributes=attributes, text=text)


def _xml_node(
    name: str,
    children: Sequence[XmlElement] = (),
    *,
    attributes: Mapping[str, str] | None = None,
    text: str | None = None,
) -> XmlElement:
    """Build a named Search API XML component without creating JSON.

    Parameters
    ----------
    name : str
        Local element name.
    children : Sequence[XmlElement], optional
        Ordered child elements.
    attributes : Mapping[str, str] or None, default None
        XML attributes and namespace declarations.
    text : str or None, default None
        Literal element text.

    Returns
    -------
    XmlElement
        Fresh native component.
    """
    node = XmlElement(f"{{{SEARCH_NS_URI}}}{name}", dict(attributes or {}))
    node.extend(children)
    node.text = text
    return node


def _json_node(
    name: str,
    children: Sequence[dict] = (),
    *,
    attributes: Mapping[str, str] | None = None,
    text: str | None = None,
) -> dict:
    """Build a named Search API JSON component without creating XML.

    Parameters
    ----------
    name : str
        Native member name.
    children : Sequence[dict], optional
        Directly serialized child components.
    attributes : Mapping[str, str] or None, default None
        Descriptor metadata.
    text : str or None, default None
        Literal lexical value.

    Returns
    -------
    dict
        Fresh JSON member; repeated children are combined into arrays.
    """
    if children or attributes:
        return {name: _json_members(children, attributes)}
    return {name: text}


def _query_pair(
    name: str,
    first: tuple[str, StructuredQuery],
    second: tuple[str, StructuredQuery],
    *,
    output_format: Literal["json", "xml"] = "xml",
) -> XmlElement | dict:
    """Build a query combining two subqueries, each in its named wrapper.

    Parameters
    ----------
    name : str
        Native member name, such as and-not-query.
    first, second : tuple[str, StructuredQuery]
        Wrapper name and subquery, such as ``("positive-query", query)``.
    output_format : {'json', 'xml'}, default 'xml'
        Requested representation.

    Returns
    -------
    xml.etree.ElementTree.Element or dict
        Fresh native component.
    """
    return _node(
        name,
        [
            _node(
                wrapper,
                _subqueries(query, output_format=output_format),
                output_format=output_format,
            )
            for wrapper, query in (first, second)
        ],
        output_format=output_format,
    )


def _subqueries(
    queries: StructuredQuery | Sequence[StructuredQuery],
    *,
    output_format: Literal["json", "xml"] = "xml",
) -> list[XmlElement | dict]:
    """Serialize nested queries, already validated by _check_subqueries.

    Parameters
    ----------
    queries : StructuredQuery or Sequence[StructuredQuery]
        Query children.
    output_format : {'json', 'xml'}, default 'xml'
        Requested serialization format.

    Returns
    -------
    list[xml.etree.ElementTree.Element or dict]
        Serialized children.
    """
    return [query.serialize(output_format) for query in _sequence(queries)]


def _check_subqueries(queries: StructuredQuery | Sequence[StructuredQuery]):
    """Reject nested queries that cannot be children of another query.

    Parameters
    ----------
    queries : StructuredQuery or Sequence[StructuredQuery]
        Query children.

    Raises
    ------
    TypeError
        If a child is not a StructuredQuery or is a top-level Query wrapper.
    """
    for query in _sequence(queries):
        if not isinstance(query, StructuredQuery) or isinstance(query, Query):
            message = (
                "Subqueries must be StructuredQuery instances, not Query wrappers."
            )
            raise TypeError(message)


def _targets(
    target: QueryTarget | Sequence[QueryTarget],
    attribute: Attribute | Sequence[Attribute] | None = None,
    *,
    output_format: Literal["json", "xml"] = "xml",
) -> list[XmlElement | dict]:
    """Serialize targets and optional element attributes, checked by _check_targets.

    Parameters
    ----------
    target : QueryTarget or Sequence[QueryTarget]
        Location descriptors.
    attribute : Attribute or Sequence[Attribute] or None, default None
        Element attributes.
    output_format : {'json', 'xml'}, default 'xml'
        Requested serialization format.

    Returns
    -------
    list[xml.etree.ElementTree.Element or dict]
        Location descriptors in XML order.
    """
    result = [item.serialize(output_format) for item in _sequence(target)]
    if attribute is not None:
        result.extend(item.serialize(output_format) for item in _sequence(attribute))
    return result


def _check_targets(
    target: QueryTarget | Sequence[QueryTarget],
    attribute: Attribute | Sequence[Attribute] | None = None,
    *,
    allow_path: bool = False,
):
    """Reject missing, mixed or unsupported target kinds and misplaced attributes.

    Parameters
    ----------
    target : QueryTarget or Sequence[QueryTarget]
        Location descriptors.
    attribute : Attribute or Sequence[Attribute] or None, default None
        Element attributes.
    allow_path : bool, default False
        Whether path range indexes are supported.

    Raises
    ------
    TypeError
        If a target is not an Element, JsonProperty or Field (or, for ranges,
        a PathIndex).
    ValueError
        If there is no target, the targets are of mixed kinds, or attributes
        accompany targets other than Element.
    """
    allowed = (Element, JsonProperty, Field, PathIndex) if allow_path else (
        Element,
        JsonProperty,
        Field,
    )
    targets = _sequence(target)
    if any(not isinstance(item, allowed) for item in targets):
        message = (
            "Targets must be Element, JsonProperty or Field instances"
            + (", or PathIndex for ranges." if allow_path else ".")
        )
        raise TypeError(message)
    kinds = {type(item) for item in targets}
    if len(kinds) != 1:
        message = "Use one non-empty target kind."
        raise ValueError(message)
    if attribute is not None and kinds != {Element}:
        message = "Attribute selectors require Element targets."
        raise ValueError(message)


def _scope(
    scope: str | None,
    *,
    output_format: Literal["json", "xml"] = "xml",
) -> list[XmlElement | dict]:
    """Serialize the optional fragment scope, checked by _check_scope.

    Parameters
    ----------
    scope : str or None
        Optional documents or properties scope.
    output_format : {'json', 'xml'}, default 'xml'
        Requested serialization format.

    Returns
    -------
    list[xml.etree.ElementTree.Element or dict]
        Optional fragment-scope child.
    """
    return _optional_children(fragment_scope=scope, output_format=output_format)


def _check_scope(scope: str | None):
    """Reject a fragment scope the Search API does not support.

    Parameters
    ----------
    scope : str or None
        Optional documents or properties scope.

    Raises
    ------
    ValueError
        If the scope is neither documents nor properties.
    """
    if scope not in (None, "documents", "properties"):
        message = "Fragment scope must be documents or properties."
        raise ValueError(message)


def _optional_children(
    *,
    output_format: Literal["json", "xml"] = "xml",
    **values: _Scalar | None,
) -> list[XmlElement | dict]:
    """Serialize supplied scalar options, omitting None but preserving false and zero.

    Parameters
    ----------
    output_format : {'json', 'xml'}, default 'xml'
        Requested representation.
    **values : str, int, float, bool, Decimal, date, datetime or None
        Option names and values; underscores in names become hyphens. JSON
        holds numbers as numbers and booleans as booleans.

    Returns
    -------
    list[xml.etree.ElementTree.Element or dict]
        Optional scalar children in supplied order.
    """
    return [
        {name.replace("_", "-"): _json_option(value)}
        if output_format == "json"
        else _node(name.replace("_", "-"), text=_lexical(value))
        for name, value in values.items()
        if value is not None
    ]


def _children(
    name: str,
    values: _Scalar | Sequence[_Scalar],
    *,
    json_array: bool = False,
    output_format: Literal["json", "xml"] = "xml",
) -> list[XmlElement | dict]:
    """Serialize scalar or repeated text children using XML lexical forms.

    Parameters
    ----------
    name : str
        Local child name.
    values : str, int, float, bool, Decimal, date, datetime or Sequence
        Child values, kept as lexical strings in JSON too. An empty sequence
        produces no children.
    json_array : bool, default False
        Whether native JSON always holds the values in an array.
    output_format : {'json', 'xml'}, default 'xml'
        Requested representation.

    Returns
    -------
    list[xml.etree.ElementTree.Element or dict]
        Text children, escaped by ElementTree during serialization.
    """
    nodes = [
        _node(name, text=_lexical(value), output_format=output_format)
        for value in _sequence(values)
    ]
    return [_as_json_array(node) for node in nodes] if json_array else nodes


def _json_option(value: _Scalar) -> str | float | bool:
    """Return the JSON scalar of a query option.

    Parameters
    ----------
    value : str, int, float, bool, Decimal, date or datetime
        Option value.

    Returns
    -------
    str, float or bool
        Booleans unchanged, numbers as floats, anything else lexical.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    return _lexical(value)


def _lexical(value: _Scalar) -> str:
    """Format a typed value for an XML text node.

    Parameters
    ----------
    value : str, int, float, bool, Decimal, date or datetime
        Atomic value.

    Returns
    -------
    str
        XML lexical representation.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, float):
        lexical = str(value)
        return {"inf": "INF", "-inf": "-INF", "nan": "NaN"}.get(lexical, lexical)
    return str(value)


def _sequence(value: _Item | Sequence[_Item]) -> Sequence[_Item]:
    """Treat a scalar as one item while preserving supplied sequences.

    Parameters
    ----------
    value : Any or Sequence
        A scalar or a sequence; strings are scalars.

    Returns
    -------
    Sequence
        The supplied sequence or a single-item tuple.
    """
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return (value,)


def _is_non_finite(value: object) -> bool:
    """Tell whether a numeric argument is infinite or NaN.

    Parameters
    ----------
    value : object
        Any argument; only floats and decimals can be non-finite.

    Returns
    -------
    bool
        True for INF, -INF or NaN.
    """
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, Decimal):
        return not value.is_finite()
    return False


def _check_json_properties(*properties: JsonProperty | None):
    """Reject geospatial JSON property selectors that are not JsonProperty.

    Parameters
    ----------
    *properties : JsonProperty or None
        Required or omitted optional property selectors.

    Raises
    ------
    TypeError
        If a supplied selector is not a JsonProperty.
    """
    if any(
        prop is not None and not isinstance(prop, JsonProperty) for prop in properties
    ):
        message = "Geospatial JSON property selectors must be JsonProperty instances."
        raise TypeError(message)


_GEOSPATIAL_OPERATORS = frozenset(get_args(_GeospatialOperator))
_TEMPORAL_OPERATORS = frozenset(get_args(_TemporalOperator))


def _is_required(item: DataclassField) -> bool:
    """Tell whether a dataclass field has no default.

    Parameters
    ----------
    item : dataclasses.Field
        A component field.

    Returns
    -------
    bool
        True when the caller must supply the argument.
    """
    return item.default is MISSING and item.default_factory is MISSING


def _check_type(
    component: object,
    name: str,
    types: type | tuple[type, ...],
    *,
    optional: bool = False,
):
    """Reject an argument of a type the component cannot serialize.

    Parameters
    ----------
    component : object
        The component being built.
    name : str
        The field holding the argument.
    types : type or tuple[type, ...]
        Accepted types.
    optional : bool, default False
        Whether None is accepted.

    Raises
    ------
    TypeError
        If the argument is not of an accepted type.
    """
    value = getattr(component, name)
    if (value is None and optional) or isinstance(value, types):
        return
    message = (
        f"{type(component).__name__}.{name} must be {_type_names(types)}, "
        f"got {type(value).__name__}"
    )
    raise TypeError(message)


def _check_types(component: object, name: str, types: type | tuple[type, ...]):
    """Reject a value or sequence item of a type the component cannot serialize.

    Parameters
    ----------
    component : object
        The component being built.
    name : str
        The field holding one value or a sequence of them.
    types : type or tuple[type, ...]
        Accepted item types.

    Raises
    ------
    TypeError
        If an item is not of an accepted type.
    """
    for value in _sequence(getattr(component, name)):
        if not isinstance(value, types):
            message = (
                f"{type(component).__name__}.{name} items must be "
                f"{_type_names(types)}, got {type(value).__name__}"
            )
            raise TypeError(message)


def _check_number(
    component: object,
    name: str,
    *,
    integer: bool = False,
    optional: bool = False,
):
    """Reject a numeric option that is not a number, or not an integer.

    Parameters
    ----------
    component : object
        The component being built.
    name : str
        The field holding the option.
    integer : bool, default False
        Whether only integers are accepted.
    optional : bool, default False
        Whether None is accepted.

    Raises
    ------
    TypeError
        If the option is a boolean or not a number of the accepted kind.
    """
    value = getattr(component, name)
    if value is None and optional:
        return
    types = (int,) if integer else (int, float, Decimal)
    if isinstance(value, bool) or not isinstance(value, types):
        expected = "an integer" if integer else "a number"
        message = (
            f"{type(component).__name__}.{name} must be {expected}, "
            f"got {type(value).__name__}"
        )
        raise TypeError(message)


def _check_choice(
    component: object,
    name: str,
    choices: frozenset[str],
    description: str,
    *,
    optional: bool = False,
):
    """Reject an enumerated argument outside its native value set.

    Parameters
    ----------
    component : object
        The component being built.
    name : str
        The field holding the argument.
    choices : frozenset[str]
        Native values.
    description : str
        What the values are, such as ``temporal operator``.
    optional : bool, default False
        Whether None is accepted.

    Raises
    ------
    ValueError
        If the argument is not a native value.
    """
    value = getattr(component, name)
    if (value is None and optional) or value in choices:
        return
    message = f"{type(component).__name__}.{name} {value!r} is not a {description}"
    raise ValueError(message)


def _type_names(types: type | tuple[type, ...]) -> str:
    """Name accepted types for an error message.

    Parameters
    ----------
    types : type or tuple[type, ...]
        Accepted types.

    Returns
    -------
    str
        For example ``str or datetime``.
    """
    types = types if isinstance(types, tuple) else (types,)
    return " or ".join(item.__name__ for item in types)
