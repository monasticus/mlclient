"""Short constructors and composition helpers for structured queries."""

from __future__ import annotations

from mlclient.search.structured import (
    AndNotQuery,
    AndQuery,
    Attribute,
    BoostQuery,
    Box,
    Circle,
    CollectionConstraintQuery,
    CollectionQuery,
    ContainerConstraintQuery,
    ContainerQuery,
    CustomConstraintQuery,
    DirectoryQuery,
    DocumentFragmentQuery,
    DocumentQuery,
    Element,
    ElementConstraintQuery,
    FalseQuery,
    Field,
    GeoAttributePairQuery,
    GeoElementPairQuery,
    GeoElementQuery,
    GeoJsonPropertyPairQuery,
    GeoJsonPropertyQuery,
    GeoPathQuery,
    GeoRegionConstraintQuery,
    GeoRegionPathQuery,
    GeospatialConstraintQuery,
    JsonProperty,
    LocksFragmentQuery,
    LsqtQuery,
    NearQuery,
    NotInQuery,
    NotQuery,
    OperatorState,
    OrQuery,
    PathIndex,
    Period,
    PeriodCompareQuery,
    PeriodRangeQuery,
    Point,
    Polygon,
    PropertiesConstraintQuery,
    PropertiesFragmentQuery,
    QtextQuery,
    Query,
    RangeConstraintQuery,
    RangeQuery,
    StructuredQuery,
    TermQuery,
    TrueQuery,
    ValueConstraintQuery,
    ValueQuery,
    WordConstraintQuery,
    WordQuery,
)

__all__ = [
    "and_",
    "and_not",
    "attribute",
    "boost",
    "box",
    "circle",
    "collection",
    "collection_constraint",
    "container",
    "container_constraint",
    "custom_constraint",
    "directory",
    "document",
    "document_fragment",
    "element",
    "element_constraint",
    "false",
    "field",
    "geo_attribute_pair",
    "geo_element",
    "geo_element_pair",
    "geo_json_property",
    "geo_json_property_pair",
    "geo_path",
    "geo_region_constraint",
    "geo_region_path",
    "geospatial_constraint",
    "json_property",
    "locks_fragment",
    "lsqt",
    "near",
    "not_",
    "not_in",
    "operator_state",
    "or_",
    "path_index",
    "period",
    "period_compare",
    "period_range",
    "point",
    "polygon",
    "properties_constraint",
    "properties_fragment",
    "qtext",
    "query",
    "range_",
    "range_constraint",
    "term",
    "true",
    "value",
    "value_constraint",
    "word",
    "word_constraint",
]

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
range_ = RangeQuery
term = TermQuery
true = TrueQuery
value_constraint = ValueConstraintQuery
value = ValueQuery
word_constraint = WordConstraintQuery
word = WordQuery


def query(*queries: StructuredQuery) -> Query:
    """Wrap structured queries for submission to the Search API.

    Parameters
    ----------
    *queries : StructuredQuery
        Top-level query components.

    Returns
    -------
    Query
        Structured-query wrapper.

    Raises
    ------
    TypeError
        If a subquery or query setting has an unsupported type.
    """
    return Query(queries)


def and_(*queries: StructuredQuery, ordered: bool | None = None) -> AndQuery:
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

    Raises
    ------
    TypeError
        If a subquery or query setting has an unsupported type.
    """
    return AndQuery(queries, ordered=ordered)


def or_(*queries: StructuredQuery) -> OrQuery:
    """Build the union of positional query components.

    Parameters
    ----------
    *queries : StructuredQuery
        Alternative queries.

    Returns
    -------
    OrQuery
        Composable union query.

    Raises
    ------
    TypeError
        If a subquery or query setting has an unsupported type.
    """
    return OrQuery(queries)


def near(
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

    Raises
    ------
    TypeError
        If a subquery or query setting has an unsupported type.
    ValueError
        If a numeric query setting is not finite.
    """
    return NearQuery(
        queries,
        distance=distance,
        minimum_distance=minimum_distance,
        distance_weight=distance_weight,
        ordered=ordered,
    )
