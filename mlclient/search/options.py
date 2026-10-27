"""Build Search API options without installing server configuration."""

from __future__ import annotations

import math
from abc import abstractmethod
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import ClassVar, Literal, get_args
from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import SubElement, tostring

from mlclient.search.base import QueryComponent, SearchQuery
from mlclient.search.structured import (
    SEARCH_NS_URI,
    Attribute,
    Element,
    Field,
    JsonProperty,
    PathIndex,
)

__all__ = [
    "AdditionalQuery",
    "Aggregate",
    "Anchor",
    "Annotation",
    "Bucket",
    "Callback",
    "Collection",
    "CollectionConstraint",
    "ComputedBucket",
    "ConcurrencyLevel",
    "ConstraintValue",
    "ContainerConstraint",
    "Control",
    "CustomConstraint",
    "Debug",
    "DefaultSuggestionSource",
    "ElementQueryConstraint",
    "ExtractDocumentData",
    "ExtractMetadata",
    "Forest",
    "FragmentScope",
    "GeoAttributePair",
    "GeoConstraint",
    "GeoElement",
    "GeoElementPair",
    "GeoJsonProperty",
    "GeoJsonPropertyPair",
    "GeoPath",
    "GeoRegionPath",
    "Grammar",
    "Heatmap",
    "Implicit",
    "Joiner",
    "MetadataQName",
    "NativeOption",
    "NativeOptions",
    "Operator",
    "OperatorState",
    "PageLength",
    "PreferredMatches",
    "PropertiesConstraint",
    "QualityWeight",
    "Range",
    "RangeConstraint",
    "ResultDecorator",
    "ReturnAggregates",
    "ReturnConstraints",
    "ReturnFacets",
    "ReturnFrequencies",
    "ReturnMetrics",
    "ReturnPlan",
    "ReturnQtext",
    "ReturnQuery",
    "ReturnResults",
    "ReturnSimilar",
    "ReturnValues",
    "SearchOption",
    "SearchOptionString",
    "SearchOptions",
    "SearchableExpression",
    "SortOrder",
    "Starter",
    "SuggestionSource",
    "Term",
    "TermDefault",
    "TransformResults",
    "Tuples",
    "Value",
    "ValueConstraint",
    "Values",
    "Word",
    "WordConstraint",
    "WordLexicon",
]

# MarkLogic's REST options converter holds these members in JSON arrays
# ($csu:array-element-names in /MarkLogic/rest-api/lib/config-query-util.xqy).
_REPEATABLE_MEMBERS = frozenset(
    {
        "annotation",
        "constraint",
        "forest",
        "operator",
        "search-option",
        "sort-order",
        "suggestion-source",
        "tuples",
        "values",
    },
)

_MIN_TUPLE_INDEXES = 2

_JsonNodeType = Literal["string", "boolean", "null", "number"]
"""JSON node type a value constraint matches."""
_JSON_NODE_TYPES = frozenset(get_args(_JsonNodeType))


@dataclass(frozen=True)
class Range(QueryComponent):
    """Describe an existing range index for values, facets or sorting.

    Parameters
    ----------
    target : Element | Field | JsonProperty | PathIndex
        Indexed element, field, JSON property or path.
    index_type : str, default 'xs:string'
        Index XML Schema type, including the xs: prefix.
    collation : str | None, default None
        String index collation; must match the database index.
    attribute : Attribute | None, default None
        Indexed attribute of an Element target.
    facet, nullable : bool | None
        Optional facet and nullable-index settings. Nullable requires XML.
    fragment_scope : {'documents', 'properties'} | None
        Fragment kind used by the index definition.
    weight : float | None
        Relevance weight.
    options, facet_options : str | Sequence[str] | None
        Native range-option and facet-option strings.
    buckets : Sequence[Bucket]
        Fixed facet intervals.
    computed_buckets : Sequence[ComputedBucket]
        Relative date/time facet intervals.
    anchors : Sequence[Anchor]
        Anchors for custom facet extensions; requires XML.
    """

    target: Element | Field | JsonProperty | PathIndex
    index_type: str = "xs:string"
    collation: str | None = None
    attribute: Attribute | None = None

    facet: bool | None = None
    nullable: bool | None = None
    fragment_scope: Literal["documents", "properties"] | None = None
    weight: float | None = None
    options: str | Sequence[str] | None = None
    facet_options: str | Sequence[str] | None = None
    buckets: Sequence[Bucket] = ()
    computed_buckets: Sequence[ComputedBucket] = ()
    anchors: Sequence[Anchor] = ()

    def __post_init__(self):
        """Reject a target or attribute the range cannot describe.

        Raises
        ------
        TypeError
            For an unsupported target, or an attribute that is not an Attribute
            of an Element target.
        """
        _matching(self.fragment_scope, self.weight)
        for bucket in self.buckets:
            _require(bucket, Bucket, "range bucket")
        for bucket in self.computed_buckets:
            _require(bucket, ComputedBucket, "computed range bucket")
        for anchor in self.anchors:
            _require(anchor, Anchor, "range anchor")
        for name, value in (("facet", self.facet), ("nullable", self.nullable)):
            if value is not None:
                _require(value, bool, name)
        object.__setattr__(self, "anchors", tuple(self.anchors))
        object.__setattr__(self, "buckets", tuple(self.buckets))
        object.__setattr__(self, "computed_buckets", tuple(self.computed_buckets))
        for name in ("options", "facet_options"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                object.__setattr__(self, name, tuple(value))
        if not isinstance(self.target, (Element, Field, JsonProperty, PathIndex)):
            message = (
                "range target must be an Element, Field, JsonProperty or PathIndex"
            )
            raise TypeError(message)
        if self.attribute is not None and (
            not isinstance(self.target, Element)
            or not isinstance(self.attribute, Attribute)
        ):
            message = "range attribute requires an Element target and an Attribute"
            raise TypeError(message)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Build a range specification directly in the requested vocabulary.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Native output format.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            A range component, without conversion between XML and JSON.
        """
        return self._json() if output_format == "json" else self._xml()

    def _json(self) -> dict:
        """Build the range index as native JSON.

        Returns
        -------
        dict
            Fresh range member including its target and optional attribute.
        """
        if self.nullable is not None:
            message = (
                "nullable range options require XML; MarkLogic's JSON converter "
                "does not preserve nullable"
            )
            raise TypeError(message)
        members = {"type": self.index_type}
        if self.collation is not None:
            members["collation"] = self.collation
        members.update(self.target.to_json())
        if self.attribute is not None:
            members.update(self.attribute.to_json())
        members.update(self._settings().to_json()["range"])
        return {"range": members}

    def _xml(self) -> XmlElement:
        """Build the range index as native XML.

        Returns
        -------
        XmlElement
            Fresh range element with its target children in native order.
        """
        attributes = {"type": self.index_type}
        if self.collation is not None:
            attributes["collation"] = self.collation
        node = XmlElement(f"{{{SEARCH_NS_URI}}}range", attributes)
        node.append(self.target.to_xml())
        if self.attribute is not None:
            node.append(self.attribute.to_xml())
        settings = self._settings().to_xml()
        node.attrib.update(settings.attrib)
        node.extend(settings)
        return node

    def _settings(self) -> _Definition:
        """Describe optional range matching, facets and bucket boundaries.

        Returns
        -------
        _Definition
            Range attributes and children, excluding the index target.
        """
        return _Definition(
            "range",
            {
                **_present({"facet": self.facet, "nullable": self.nullable}),
                **_option_members("facet-option", self.facet_options),
                **_option_members("range-option", self.options),
            },
            (
                *_scalars(
                    {"fragment-scope": self.fragment_scope, "weight": self.weight},
                ),
                *self.buckets,
                *self.computed_buckets,
                *self.anchors,
            ),
            repeatable=frozenset({"bucket", "computed-bucket", "anchor"}),
        )


class _OptionComponent(QueryComponent):
    """Serialize an immutable option component in its requested native form."""

    _definition: _Definition

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize this option without converting through the other format.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested native vocabulary.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Independent native representation of this option.
        """
        return self._definition.serialize(output_format)


class SearchOption(_OptionComponent):
    """One immutable, typed Search API option.

    Concrete options serialize independently to native JSON members or an XML
    element. Compose them with SearchOptions or opt.options; they perform no I/O.
    """

    _definition: _Definition

    @abstractmethod
    def __init__(self):
        """Create a concrete option from its typed parameters."""
        raise NotImplementedError

    @property
    def option_name(self) -> str:
        """Return the native top-level member this option defines.

        Returns
        -------
        str
            Search API member name, such as constraint or page-length.
        """
        return self._definition.name


@dataclass(frozen=True, init=False, eq=False, repr=False)
class SearchOptions(QueryComponent):
    """Compose immutable Search API options without configuring the server.

    Parameters
    ----------
    *options : SearchOption | SearchOptions
        Typed option components or reusable groups, in serialization order.
        Repeatable members accumulate; the last non-repeatable member wins.

    Attributes
    ----------
    components : tuple[SearchOption, ...]
        Ordered immutable components after flattening groups and replacing
        non-repeatable members. Components expose their native option_name
        and independent JSON/XML serialization.

    Raises
    ------
    TypeError
        If a component is neither a SearchOption nor a SearchOptions group.
    """

    components: tuple[SearchOption, ...]
    namespaces: Mapping[str, str]

    def __init__(
        self,
        *options: SearchOption | SearchOptions,
        namespaces: Mapping[str, str] | None = None,
    ):
        """Snapshot option composition while retaining immutable components.

        Parameters
        ----------
        *options : SearchOption | SearchOptions
            Individual options or reusable option groups.
        namespaces : Mapping[str, str] | None
            Prefix bindings for grammar QNames and custom extension data.
            Nested group bindings are merged; explicit bindings take precedence.

        Raises
        ------
        TypeError
            If a component has an unsupported type.
        """
        bindings = {}
        components = []
        for option in options:
            if isinstance(option, SearchOptions):
                additions = option.components
                bindings.update(option.namespaces)
            elif isinstance(option, SearchOption):
                additions = (option,)
            else:
                message = (
                    "options components must be SearchOption or SearchOptions instances"
                )
                raise TypeError(message)
            for component in additions:
                if component.option_name not in _REPEATABLE_MEMBERS:
                    components = [
                        held
                        for held in components
                        if held.option_name != component.option_name
                    ]
                components.append(component)
        object.__setattr__(self, "components", tuple(components))
        bindings.update(namespaces or {})
        object.__setattr__(self, "namespaces", _namespace_bindings(bindings))

    def __eq__(self, other: object) -> bool:
        """Compare options by their independent native representations.

        Parameters
        ----------
        other : object
            Another object.

        Returns
        -------
        bool
            True for a SearchOptions with the same definitions in the same order.
        """
        if not isinstance(other, SearchOptions):
            return NotImplemented
        return self.to_json() == other.to_json() and tostring(
            self.to_xml(),
        ) == tostring(other.to_xml())

    def __repr__(self) -> str:
        """Name the native definitions in insertion order.

        Returns
        -------
        str
            For example ``SearchOptions(values, page-length)``.
        """
        names = ", ".join(component.option_name for component in self.components)
        return f"SearchOptions({names})"

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Build the selected native options representation from the definitions.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Native output format.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            A defensive copy with the options wrapper: repeatable members as
            JSON lists, the others as single values.
        """
        return self._json() if output_format == "json" else self._xml()

    def _xml(self) -> XmlElement:
        """Build the options wrapper and ordered native XML definitions.

        Returns
        -------
        XmlElement
            Fresh options tree.
        """
        node = XmlElement(f"{{{SEARCH_NS_URI}}}options")
        node.extend([component.to_xml() for component in self.components])
        for prefix, uri in self.namespaces.items():
            if (
                prefix == "cts"
                and uri == "http://marklogic.com/cts"
                and any(
                    child.tag.startswith("{http://marklogic.com/cts}")
                    for child in node.iter()
                )
            ):
                continue
            node.set(f"xmlns:{prefix}", uri)
        return node

    def _json(self) -> dict:
        """Build native JSON with arrays for repeatable definitions.

        Returns
        -------
        dict
            Fresh options object.
        """
        members: dict = {}
        if self.namespaces:
            members["namespaces"] = dict(self.namespaces)
        for component in self.components:
            name = component.option_name
            definition = component.to_json()[name]
            if name in _REPEATABLE_MEMBERS:
                members.setdefault(name, []).append(definition)
            else:
                members[name] = definition
        return {"options": members}

    __hash__ = None


@dataclass(frozen=True, init=False)
class Values(SearchOption):
    """Define a named range, URI or collection lexicon."""

    name: str
    index: (
        Range
        | GeoElement
        | GeoElementPair
        | GeoAttributePair
        | GeoJsonProperty
        | GeoJsonPropertyPair
        | GeoPath
        | Collection
        | Literal["uri", "collection"]
    )
    options: str | Sequence[str] | None
    style: str | None
    aggregates: tuple[Aggregate, ...]
    annotation: str | None

    def __init__(
        self,
        name: str,
        index: Range
        | GeoElement
        | GeoElementPair
        | GeoAttributePair
        | GeoJsonProperty
        | GeoJsonPropertyPair
        | GeoPath
        | Collection
        | Literal["uri", "collection"],
        *,
        options: str | Sequence[str] | None = None,
        style: Literal["default", "consistent"] | None = None,
        aggregates: Sequence[Aggregate] = (),
        annotation: str | None = None,
    ):
        """Define a named range, URI or collection lexicon.

        Parameters
        ----------
        name : str
            Values definition name passed to SearchService.values or aggregate.
        index : Range | {'uri', 'collection'}
            Existing range index or enabled database lexicon.
        options : str | Sequence[str] | None, default None
            Native values-option strings, such as frequency-order.
        style : {'default', 'consistent'} | None
            Lexicon result style.
        aggregates : Sequence[Aggregate]
            Built-in or native plugin aggregates.
        annotation : str | None
            Values definition description.

        Raises
        ------
        TypeError
            For an unsupported index specification.
        """
        _style(style)
        for aggregate in aggregates:
            _require(aggregate, Aggregate, "lexicon aggregate")
        object.__setattr__(self, "style", style)
        object.__setattr__(self, "aggregates", tuple(aggregates))
        object.__setattr__(self, "annotation", annotation)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "index", index)
        object.__setattr__(
            self,
            "options",
            options if options is None or isinstance(options, str) else tuple(options),
        )
        if not isinstance(index, (Range, _Geospatial, Collection)) and index not in (
            "uri",
            "collection",
        ):
            message = (
                "values index must be a Range, geospatial index, Collection, uri "
                "or collection"
            )
            raise TypeError(message)
        target = (
            index
            if isinstance(index, QueryComponent)
            else _Definition(index, value=None)
        )
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "values",
                {
                    **_present({"name": name, "style": style}),
                    **_option_members("values-option", options),
                },
                (target, *self.aggregates, *_scalars({"annotation": annotation})),
                repeatable=frozenset({"aggregate", "annotation"}),
            ),
        )


@dataclass(frozen=True, init=False)
class Tuples(SearchOption):
    """Define co-occurring values from two or more indexes or lexicons."""

    name: str
    indexes: tuple[QueryComponent | str, ...]
    options: tuple[str, ...] | None
    style: str | None
    aggregates: tuple[Aggregate, ...]
    annotation: str | None

    def __init__(
        self,
        name: str,
        *indexes: Range
        | GeoElement
        | GeoElementPair
        | GeoAttributePair
        | GeoJsonProperty
        | GeoJsonPropertyPair
        | GeoPath
        | Collection
        | Literal["uri", "collection"],
        options: str | Sequence[str] | None = None,
        style: Literal["default", "consistent"] | None = None,
        aggregates: Sequence[Aggregate] = (),
        annotation: str | None = None,
    ):
        """Define co-occurring values from two or more indexes or lexicons.

        Parameters
        ----------
        name : str
            Tuples definition name passed to SearchService.tuples or aggregate.
        *indexes : Range
            Two or more indexes or URI/collection lexicons, in tuple order.
        options : str | Sequence[str] | None
            Native values-option strings.
        style : {'default', 'consistent'} | None
            Lexicon result style.
        aggregates : Sequence[Aggregate]
            Built-in or native plugin aggregates.
        annotation : str | None
            Tuples definition description.

        Raises
        ------
        ValueError
            If fewer than two indexes are supplied.
        TypeError
            If an index is not a supported range, geospatial or lexicon definition.
        """
        object.__setattr__(
            self,
            "options",
            None if options is None else tuple(_strings(options)),
        )
        _style(style)
        for aggregate in aggregates:
            _require(aggregate, Aggregate, "lexicon aggregate")
        object.__setattr__(self, "style", style)
        object.__setattr__(self, "aggregates", tuple(aggregates))
        object.__setattr__(self, "annotation", annotation)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "indexes", indexes)
        if len(indexes) < _MIN_TUPLE_INDEXES:
            message = "tuples requires at least two indexes"
            raise ValueError(message)
        if any(
            not isinstance(index, (Range, _Geospatial, Collection))
            and index not in ("uri", "collection")
            for index in indexes
        ):
            message = (
                "tuples indexes must be Range, geospatial, Collection, uri or "
                "collection definitions"
            )
            raise TypeError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "tuples",
                {
                    **_present({"name": name, "style": style}),
                    **_option_members("values-option", options),
                },
                (
                    *tuple(
                        index
                        if isinstance(index, QueryComponent)
                        else _Definition(index, value=None)
                        for index in indexes
                    ),
                    *self.aggregates,
                    *_scalars({"annotation": annotation}),
                ),
                repeatable=frozenset({"aggregate", "annotation"}),
            ),
        )


@dataclass(frozen=True, init=False)
class RangeConstraint(SearchOption):
    """Define a named range constraint and optional facet."""

    name: str
    index: Range
    facet: bool
    options: str | Sequence[str] | None

    annotation: str | None

    def __init__(
        self,
        name: str,
        index: Range,
        *,
        facet: bool = True,
        options: str | Sequence[str] | None = None,
        annotation: str | None = None,
    ):
        """Define a named range constraint and optional facet.

        Parameters
        ----------
        name : str
            Constraint name used by string queries and returned facets.
        index : Range
            Existing range index.
        facet : bool, default True
            Whether to calculate a facet.
        options : str | Sequence[str] | None, default None
            Native facet-option strings, such as limit=10.
        annotation : str | None
            Constraint description.

        Raises
        ------
        TypeError
            If index is not a supported index or native sort marker.
        """
        object.__setattr__(self, "annotation", annotation)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "index", index)
        object.__setattr__(self, "facet", facet)
        object.__setattr__(
            self,
            "options",
            options if options is None or isinstance(options, str) else tuple(options),
        )
        if not isinstance(index, Range):
            message = "range constraint index must be a Range"
            raise TypeError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "constraint",
                {"name": name},
                (
                    _Definition(
                        "range",
                        {"facet": facet, **_option_members("facet-option", options)},
                        index=index,
                    ),
                    *_scalars({"annotation": annotation}),
                ),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True, init=False)
class WordConstraint(SearchOption):
    """Define a named word constraint on an element, JSON property or field."""

    name: str
    target: Element | JsonProperty | Field
    attribute: Attribute | None
    options: str | Sequence[str] | None

    fragment_scope: str | None
    weight: float | None
    collation: str | None
    annotation: str | None

    def __init__(
        self,
        name: str,
        target: Element | JsonProperty | Field,
        *,
        attribute: Attribute | None = None,
        options: str | Sequence[str] | None = None,
        fragment_scope: Literal["documents", "properties"] | None = None,
        weight: float | None = None,
        annotation: str | None = None,
        collation: str | None = None,
    ):
        """Define a named word constraint on an element, JSON property or field.

        String queries use it as ``name:word``; WordConstraintQuery names it.

        Parameters
        ----------
        name : str
            Constraint name.
        target : Element | JsonProperty | Field
            The element, JSON property or field whose words are matched.
        attribute : Attribute | None, default None
            Attribute of an Element target whose words are matched instead.
        options : str | Sequence[str] | None, default None
            Native term-option strings, such as case-insensitive.
        fragment_scope : {'documents', 'properties'} | None
            Fragment kind matched by the constraint.
        weight : float | None
            Relevance weight.
        annotation : str | None
            Description returned when constraints are requested.
        collation : str | None
            Word lexicon collation used for suggestions.

        Raises
        ------
        TypeError
            If target is not an Element, JsonProperty or Field, or attribute is
            not an Attribute of an Element target.
        """
        object.__setattr__(self, "collation", collation)
        object.__setattr__(self, "fragment_scope", fragment_scope)
        object.__setattr__(self, "weight", weight)
        object.__setattr__(self, "annotation", annotation)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "attribute", attribute)
        object.__setattr__(
            self,
            "options",
            options if options is None or isinstance(options, str) else tuple(options),
        )
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "constraint",
                {"name": name},
                (
                    Word(target, attribute, options, fragment_scope, weight, collation),
                    *_scalars({"annotation": annotation}),
                ),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True, init=False)
class ValueConstraint(SearchOption):
    """Define a named value constraint on an element, JSON property or field."""

    name: str
    target: Element | JsonProperty | Field
    attribute: Attribute | None
    node_type: _JsonNodeType | None
    options: str | Sequence[str] | None

    fragment_scope: str | None
    weight: float | None
    annotation: str | None

    def __init__(
        self,
        name: str,
        target: Element | JsonProperty | Field,
        *,
        attribute: Attribute | None = None,
        node_type: _JsonNodeType | None = None,
        options: str | Sequence[str] | None = None,
        fragment_scope: Literal["documents", "properties"] | None = None,
        weight: float | None = None,
        annotation: str | None = None,
    ):
        """Define a named value constraint on an element, JSON property or field.

        String queries use it as ``name:value``; ValueConstraintQuery names it.

        Parameters
        ----------
        name : str
            Constraint name.
        target : Element | JsonProperty | Field
            The element, JSON property or field whose whole value is matched.
        attribute : Attribute | None, default None
            Attribute of an Element target whose value is matched instead.
        node_type : {'string', 'boolean', 'null', 'number'} | None, default None
            JSON node type of the matched values; None matches strings, as
            MarkLogic does. Only JSON content has these node types.
        options : str | Sequence[str] | None, default None
            Native term-option strings, such as case-insensitive.
        fragment_scope : {'documents', 'properties'} | None
            Fragment kind matched by the constraint.
        weight : float | None
            Relevance weight.
        annotation : str | None
            Description returned when constraints are requested.

        Raises
        ------
        TypeError
            If target is not an Element, JsonProperty or Field, or attribute is
            not an Attribute of an Element target.
        ValueError
            If node_type is not a JSON node type.
        """
        object.__setattr__(self, "fragment_scope", fragment_scope)
        object.__setattr__(self, "weight", weight)
        object.__setattr__(self, "annotation", annotation)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "attribute", attribute)
        object.__setattr__(self, "node_type", node_type)
        object.__setattr__(
            self,
            "options",
            options if options is None or isinstance(options, str) else tuple(options),
        )
        if node_type is not None and node_type not in _JSON_NODE_TYPES:
            message = (
                "value constraint node_type must be one of "
                f"{', '.join(sorted(_JSON_NODE_TYPES))}, got {node_type!r}"
            )
            raise ValueError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "constraint",
                {"name": name},
                (
                    Value(
                        target,
                        attribute,
                        node_type,
                        options,
                        fragment_scope,
                        weight,
                    ),
                    *_scalars({"annotation": annotation}),
                ),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True, init=False)
class CollectionConstraint(SearchOption):
    """Define a named collection constraint and optional facet."""

    name: str
    prefix: str | None
    facet: bool
    options: tuple[str, ...] | None
    annotation: str | None

    def __init__(
        self,
        name: str,
        *,
        prefix: str | None = None,
        facet: bool = True,
        options: str | Sequence[str] | None = None,
        annotation: str | None = None,
    ):
        """Define a named collection constraint and optional facet.

        String queries use it as ``name:collection``, matched after the prefix.

        Parameters
        ----------
        name : str
            Constraint name.
        prefix : str | None, default None
            Collection URI prefix the constraint values are appended to.
        facet : bool, default True
            Whether to calculate a facet, which needs the collection lexicon;
            MarkLogic also calculates it by default.
        options : str | Sequence[str] | None
            Native facet-option strings.
        annotation : str | None
            Constraint description.
        """
        object.__setattr__(
            self,
            "options",
            None if options is None else tuple(_strings(options)),
        )
        object.__setattr__(self, "annotation", annotation)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "prefix", prefix)
        object.__setattr__(self, "facet", facet)
        attributes = {"facet": facet}
        if prefix is not None:
            attributes["prefix"] = prefix
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "constraint",
                {"name": name},
                (
                    _Definition(
                        "collection",
                        {**attributes, **_option_members("facet-option", options)},
                    ),
                    *_scalars({"annotation": annotation}),
                ),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True, init=False)
class ContainerConstraint(SearchOption):
    """Define a named container constraint on an element or JSON property."""

    name: str
    target: Element | JsonProperty
    fragment_scope: str | None
    annotation: str | None

    def __init__(
        self,
        name: str,
        target: Element | JsonProperty,
        *,
        fragment_scope: Literal["documents", "properties"] | None = None,
        annotation: str | None = None,
    ):
        """Define a named container constraint on an element or JSON property.

        ContainerConstraintQuery names it to match a query within the container.

        Parameters
        ----------
        name : str
            Constraint name.
        target : Element | JsonProperty
            The containing element or JSON property.
        fragment_scope : {'documents', 'properties'} | None
            Fragment kind matched inside the container.
        annotation : str | None
            Constraint description.

        Raises
        ------
        TypeError
            If target is not an Element or JsonProperty.
        """
        object.__setattr__(self, "fragment_scope", fragment_scope)
        object.__setattr__(self, "annotation", annotation)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "target", target)
        if not isinstance(target, (Element, JsonProperty)):
            message = "container constraint target must be an Element or JsonProperty"
            raise TypeError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "constraint",
                {"name": name},
                (
                    _Definition(
                        "container",
                        children=(
                            target,
                            *_scalars({"fragment-scope": fragment_scope}),
                        ),
                    ),
                    *_scalars({"annotation": annotation}),
                ),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True, init=False)
class SortOrder(SearchOption):
    """Append an index-based or native sort key in insertion order."""

    index: (
        Range
        | Literal[
            "score",
            "score-order",
            "confidence-order",
            "document-order",
            "fitness-order",
            "quality-order",
            "unordered",
        ]
    )
    direction: Literal["ascending", "descending"]

    annotation: str | None

    def __init__(
        self,
        index: Range
        | Literal[
            "score",
            "score-order",
            "confidence-order",
            "document-order",
            "fitness-order",
            "quality-order",
            "unordered",
        ],
        *,
        direction: Literal["ascending", "descending"] = "ascending",
        annotation: str | None = None,
    ):
        """Append an index-based or native sort key in insertion order.

        Parameters
        ----------
        index : Range | str
            Index selector (facet settings are ignored), or a native marker such
            as score or unordered.
        direction : {'ascending', 'descending'}, default 'ascending'
            Sort direction.
        annotation : str | None
            Sort key description.

        Raises
        ------
        TypeError
            If index is not a supported index or native sort marker.
        ValueError
            If direction is unsupported.
        """
        object.__setattr__(self, "annotation", annotation)
        object.__setattr__(self, "index", index)
        object.__setattr__(self, "direction", direction)
        if not isinstance(index, Range) and index not in (
            "score",
            "score-order",
            "confidence-order",
            "document-order",
            "fitness-order",
            "quality-order",
            "unordered",
        ):
            message = "sort index must be a Range or a native sort marker"
            raise TypeError(message)
        if direction not in ("ascending", "descending"):
            message = "sort direction must be ascending or descending"
            raise ValueError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "sort-order",
                {"direction": direction},
                index=replace(
                    index,
                    facet=None,
                    nullable=None,
                    fragment_scope=None,
                    weight=None,
                    options=None,
                    facet_options=None,
                    buckets=(),
                    computed_buckets=(),
                    anchors=(),
                )
                if isinstance(index, Range)
                else None,
                children=(
                    *(
                        ()
                        if isinstance(index, Range)
                        else (_Definition(index, value=None),)
                    ),
                    *_scalars({"annotation": annotation}),
                ),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True, init=False)
class Control(SearchOption):
    """Set a scalar top-level option such as page-length or return-facets."""

    name: str
    value: str | int | float | bool

    def __init__(self, name: str, value: str | int | float | bool):
        """Set a scalar top-level option such as page-length or return-facets.

        A repeatable option such as search-option accumulates; any other
        replaces an earlier value.

        Parameters
        ----------
        name : str
            Native Search API scalar option name, including hyphens.
        value : str | int | float | bool
            Native scalar value. Use native definitions for complex options.

        Raises
        ------
        TypeError
            If value is not a string, number or boolean.
        ValueError
            If a float value is not finite.
        """
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "value", value)
        if not isinstance(value, (str, int, float, bool)):
            message = "control value must be a string, number or boolean"
            raise TypeError(message)
        if isinstance(value, float) and (not math.isfinite(value)):
            message = "control value must be finite"
            raise ValueError(message)
        object.__setattr__(self, "_definition", _Definition(name, value=value))


@dataclass(frozen=True, init=False, eq=False)
class NativeOption(SearchOption):
    """Preserve one caller-supplied option in its independent native formats.

    Parameters
    ----------
    definition : dict
        One JSON option definition, keyed by its native member name.
    element : xml.etree.ElementTree.Element
        Matching XML element in the Search API namespace.

    Raises
    ------
    ValueError
        If the native names, namespace or definition counts do not match.
    """

    def __init__(self, definition: dict, element: XmlElement):
        """Snapshot the JSON value and corresponding XML element.

        Parameters
        ----------
        definition : dict
            One named native JSON option.
        element : xml.etree.ElementTree.Element
            The same option in native XML.

        Raises
        ------
        ValueError
            If JSON and XML do not describe exactly one same-named option.
        """
        (matched,) = _pair_native_definitions(definition, (element,))
        object.__setattr__(self, "_definition", matched)

    def __eq__(self, other: object) -> bool:
        """Compare native options using both independent formats.

        Parameters
        ----------
        other : object
            Another object.

        Returns
        -------
        bool
            True for equal native JSON and XML; False for other objects.
        """
        if not isinstance(other, NativeOption):
            return NotImplemented
        return self.to_json() == other.to_json() and tostring(
            self.to_xml(),
        ) == tostring(other.to_xml())

    __hash__ = None


@dataclass(frozen=True, init=False, eq=False, repr=False)
class NativeOptions(SearchOptions):
    """Supply native JSON and XML for options without a typed constructor.

    Parameters
    ----------
    definition : dict
        Native options members, without an options wrapper.
    *elements : xml.etree.ElementTree.Element
        Matching search-namespace XML elements, one per JSON definition.

    Raises
    ------
    ValueError
        If the native definitions do not have matching names and counts.
    """

    def __init__(self, definition: dict, *elements: XmlElement):
        """Snapshot independent native forms for reuse in option compositions.

        Parameters
        ----------
        definition : dict
            JSON options members.
        *elements : xml.etree.ElementTree.Element
            Corresponding XML children in the Search API namespace.

        Raises
        ------
        ValueError
            If native names, namespaces or definition counts do not match.
        """
        matched = _pair_native_definitions(definition, elements)
        super().__init__(
            *(
                NativeOption({member.name: member.native[0]}, member.native[1])
                for member in matched
            ),
        )


@dataclass(frozen=True, init=False)
class PageLength(SearchOption):
    """Set the positive number of search results per page."""

    value: int

    def __init__(self, value: int):
        """Create a typed page-length option.

        Parameters
        ----------
        value : int
            Positive number of results.

        Raises
        ------
        TypeError
            If value is not an integer, or is a boolean.
        ValueError
            If value is not positive.
        """
        if type(value) is not int:
            message = "page length must be an integer"
            raise TypeError(message)
        if value <= 0:
            message = "page length must be positive"
            raise ValueError(message)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "_definition", _Definition("page-length", value=value))


@dataclass(frozen=True, init=False)
class ReturnFacets(SearchOption):
    """Choose whether the search report includes facets."""

    value: bool

    def __init__(self, value: bool):
        """Create a typed return-facets option.

        Parameters
        ----------
        value : bool
            Whether to include facets.

        Raises
        ------
        TypeError
            If value is not a boolean.
        """
        if not isinstance(value, bool):
            message = "return facets must be a boolean"
            raise TypeError(message)
        object.__setattr__(self, "value", value)
        object.__setattr__(
            self,
            "_definition",
            _Definition("return-facets", value=value),
        )


@dataclass(frozen=True)
class _Definition(QueryComponent):
    """One options member held as data, not generated JSON/XML.

    Parameters
    ----------
    name : str
        Native options member name.
    attributes : dict
        Named JSON values: scalars become XML attributes; option lists become
        repeated XML children after the target components.
    children : tuple[QueryComponent, ...]
        Nested targets, ranges and options; serialized in the requested format.
    index : Range | None
        Range whose contents are included in this member.
    value : object
        Scalar member value; Ellipsis denotes a member with attributes/children.
    native : tuple[object, XmlElement] | None
        Caller-supplied NativeOptions forms; no format conversion is performed.
    repeatable : frozenset[str]
        Child names represented as JSON arrays even for a single child.
    text_member : str | None
        JSON member whose value is XML text rather than an attribute.
    namespaces : dict[str, str]
        Prefix bindings on an extraction container.
    """

    name: str
    attributes: dict = field(default_factory=dict)
    children: tuple[QueryComponent, ...] = ()
    index: Range | None = None
    value: object = ...
    native: tuple[object, XmlElement] | None = None
    repeatable: frozenset[str] = frozenset()
    text_member: str | None = None
    namespaces: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Snapshot mutable inputs without serializing nested components."""
        # Targets and ranges are immutable and already snapshot namespace mappings.
        for name in ("attributes", "value", "native", "namespaces"):
            object.__setattr__(self, name, deepcopy(getattr(self, name)))

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Build only the requested representation of this member.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested native vocabulary.

        Returns
        -------
        dict or XmlElement
            Fresh options member, including serialized children.
        """
        if self.native is not None:
            return (
                {self.name: deepcopy(self.native[0])}
                if output_format == "json"
                else deepcopy(self.native[1])
            )
        return self._json() if output_format == "json" else self._xml()

    def _xml(self) -> XmlElement:
        """Build this definition and its children as native XML.

        Returns
        -------
        XmlElement
            Fresh member with scalar attributes and repeated option children.
        """
        node = (
            self.index.to_xml()
            if self.index is not None
            else XmlElement(
                f"{{{SEARCH_NS_URI}}}{self.name}",
            )
        )
        node.tag = f"{{{SEARCH_NS_URI}}}{self.name}"
        for prefix, uri in self.namespaces.items():
            node.set(f"xmlns:{prefix}", uri)
        for name, value in self.attributes.items():
            if name == self.text_member:
                node.text = str(value)
                continue
            if isinstance(value, list):
                continue
            node.set(
                {"cts-element": "element", "cts-options": "options"}.get(name, name),
                str(value).lower() if isinstance(value, bool) else str(value),
            )
        if self.value is not ... and self.value is not None:
            node.text = (
                str(self.value).lower()
                if isinstance(self.value, bool)
                else str(self.value)
            )
        node.extend([child.to_xml() for child in self.children])
        for name, values in self.attributes.items():
            if isinstance(values, list):
                _replace_list_children(node, name, values)
        return node

    def _json(self) -> dict:
        """Build this definition and its children as native JSON.

        Returns
        -------
        dict
            One named member; tuple indexes retain their order and native wrappers.
        """
        if self.value is not ...:
            return {self.name: deepcopy(self.value)}
        members = self.index.to_json()["range"] if self.index is not None else {}
        members.update(deepcopy(self.attributes))
        if self.namespaces:
            members["namespaces"] = deepcopy(self.namespaces)
        for child in self.children:
            for name, value in child.to_json().items():
                if self.name == "tuples" and name in {
                    "range",
                    "collection",
                    "uri",
                    "geo-elem",
                    "geo-elem-pair",
                    "geo-attr-pair",
                    "geo-json-property",
                    "geo-json-property-pair",
                    "geo-path",
                    "geo-region-path",
                }:
                    members.setdefault("indexes", []).append({name: value})
                elif name in self.repeatable:
                    members.setdefault(name, []).append(value)
                else:
                    members[name] = value
        return {self.name: members}


def _pair_native_definitions(
    definition: dict,
    elements: tuple[XmlElement, ...],
) -> list[_Definition]:
    """Match caller-supplied JSON members to their XML elements.

    Parameters
    ----------
    definition : dict
        Native JSON options members.
    elements : tuple[xml.etree.ElementTree.Element, ...]
        Native XML options children.

    Returns
    -------
    list[_Definition]
        Definitions in JSON member order; the definitions of a repeatable
        member pair with same-named elements in element order.

    Raises
    ------
    ValueError
        If an element is outside the search namespace, or a member's JSON and
        XML definition counts differ.
    """
    xml_by_name: dict[str, list[XmlElement]] = {}
    for element in elements:
        namespace, local_name = _split_clark_name(element.tag)
        if namespace != SEARCH_NS_URI:
            message = (
                "native options require XML elements in the "
                f"{SEARCH_NS_URI} namespace; "
                f"got {element.tag}"
            )
            raise ValueError(message)
        xml_by_name.setdefault(local_name, []).append(element)
    json_by_name = {
        name: _definitions_of(name, value) for name, value in definition.items()
    }
    for name in [*json_by_name, *(n for n in xml_by_name if n not in json_by_name)]:
        json_count = len(json_by_name.get(name, []))
        xml_count = len(xml_by_name.get(name, []))
        if json_count != xml_count:
            message = (
                "native options require one search-namespace XML element per JSON "
                f"definition; {name} has {json_count} JSON and {xml_count} XML "
                "definitions"
            )
            raise ValueError(message)
    return [
        _Definition(name, native=(item, node))
        for name, items in json_by_name.items()
        for item, node in zip(items, xml_by_name.get(name, []), strict=True)
    ]


def _term_target(
    kind: Literal["word", "value"],
    target: Element | JsonProperty | Field,
    attribute: Attribute | None,
) -> tuple[QueryComponent, ...]:
    """Describe what a word or value constraint matches.

    Parameters
    ----------
    kind : {'word', 'value'}
        Native constraint kind.
    target : Element | JsonProperty | Field
        The matched element, JSON property or field.
    attribute : Attribute | None
        Matched attribute of an Element target.

    Returns
    -------
    tuple[QueryComponent, ...]
        Validated components, without constructing their serialized forms.

    Raises
    ------
    TypeError
        If target is not an Element, JsonProperty or Field, or attribute is
        not an Attribute of an Element target.
    """
    if not isinstance(target, (Element, JsonProperty, Field)):
        message = f"{kind} constraint target must be an Element, JsonProperty or Field"
        raise TypeError(message)
    if attribute is not None and (
        not isinstance(target, Element) or not isinstance(attribute, Attribute)
    ):
        message = (
            f"{kind} constraint attribute requires an Element target and an Attribute"
        )
        raise TypeError(message)
    return (target,) if attribute is None else (target, attribute)


def _definitions_of(name: str, value: object) -> list:
    """Return the JSON definitions one options member holds.

    Parameters
    ----------
    name : str
        Native member name.
    value : object
        Its JSON value.

    Returns
    -------
    list
        For a repeatable member, each item of a list or the single value;
        otherwise the value as one definition, even when it is a list.
    """
    if name in _REPEATABLE_MEMBERS and isinstance(value, list):
        return value
    return [value]


def _split_clark_name(tag: str) -> tuple[str, str]:
    """Split an ElementTree tag into its namespace URI and local name.

    Parameters
    ----------
    tag : str
        A Clark-notation tag such as ``{uri}name``, or an unqualified name.

    Returns
    -------
    tuple[str, str]
        The namespace URI (empty when unqualified) and the local name.
    """
    if not tag.startswith("{"):
        return "", tag
    namespace, _, local_name = tag[1:].partition("}")
    return namespace, local_name


def _option_members(
    member: str,
    options: str | Sequence[str] | None,
) -> dict[str, list[str]]:
    """Capture option strings without creating either native representation.

    Parameters
    ----------
    member : str
        Native option member name, such as term-option.
    options : str | Sequence[str] | None
        One option string, several, or None for none.

    Returns
    -------
    dict[str, list[str]]
        One JSON option member, preserving an explicitly supplied empty list.
    """
    return {} if options is None else {member: _strings(options)}


def _strings(values: str | Sequence[str]) -> list[str]:
    """Return option strings as a list, treating one string as one option.

    Parameters
    ----------
    values : str | Sequence[str]
        One option or several.

    Returns
    -------
    list[str]
        A fresh list of the options.
    """
    return [values] if isinstance(values, str) else list(values)


@dataclass(frozen=True)
class _BooleanOption(SearchOption):
    """Hold one strictly boolean Search API control.

    Parameters
    ----------
    value : bool
        Whether to enable this control.
    """

    value: bool
    _name: ClassVar[str]

    def __post_init__(self):
        """Validate the boolean before constructing either native format.

        Raises
        ------
        TypeError
            If value is not a boolean.
        """
        if not isinstance(self.value, bool):
            message = f"{self._name} must be a boolean"
            raise TypeError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(self._name, value=self.value),
        )


class Debug(_BooleanOption):
    """Set the native debug boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "debug"


class ReturnAggregates(_BooleanOption):
    """Set the native return-aggregates boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-aggregates"


class ReturnConstraints(_BooleanOption):
    """Set the native return-constraints boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-constraints"


class ReturnFrequencies(_BooleanOption):
    """Set the native return-frequencies boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-frequencies"


class ReturnMetrics(_BooleanOption):
    """Set the native return-metrics boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-metrics"


class ReturnPlan(_BooleanOption):
    """Set the native return-plan boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-plan"


class ReturnQtext(_BooleanOption):
    """Set the native return-qtext boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-qtext"


class ReturnQuery(_BooleanOption):
    """Set the native return-query boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-query"


class ReturnResults(_BooleanOption):
    """Set the native return-results boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-results"


class ReturnSimilar(_BooleanOption):
    """Set the native return-similar boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-similar"


class ReturnValues(_BooleanOption):
    """Set the native return-values boolean control.

    Parameters
    ----------
    value : bool
        Whether to enable this report or diagnostic control.
    """

    _name = "return-values"


@dataclass(frozen=True)
class ConcurrencyLevel(SearchOption):
    """Set concurrency-level.

    Parameters
    ----------
    value : int
        Maximum number of concurrent lexicon tasks.
    """

    value: int

    def __post_init__(self):
        """Validate and capture the control.

        Raises
        ------
        ValueError
            If value is not a valid concurrency-level value.
        """
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, int)
            or self.value < 1
        ):
            message = "concurrency-level must be a positive integer"
            raise ValueError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition("concurrency-level", value=self.value),
        )


@dataclass(frozen=True)
class QualityWeight(SearchOption):
    """Set quality-weight.

    Parameters
    ----------
    value : float
        Document quality contribution to relevance scoring.
    """

    value: float

    def __post_init__(self):
        """Validate and capture the control.

        Raises
        ------
        ValueError
            If value is not a valid quality-weight value.
        """
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not math.isfinite(self.value)
        ):
            message = "quality-weight must be a finite number"
            raise ValueError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition("quality-weight", value=self.value),
        )


@dataclass(frozen=True)
class Forest(SearchOption):
    """Set forest.

    Parameters
    ----------
    value : str | int
        Forest ID; compose several Forest instances to restrict multiple forests.
    """

    value: str | int

    def __post_init__(self):
        """Validate and capture the control.

        Raises
        ------
        TypeError
            If value is not a valid forest value.
        """
        if isinstance(self.value, bool) or not isinstance(self.value, (str, int)):
            message = "forest must be a string or integer ID"
            raise TypeError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition("forest", value=str(self.value)),
        )


@dataclass(frozen=True)
class FragmentScope(SearchOption):
    """Set fragment-scope.

    Parameters
    ----------
    value : Literal["documents", "properties"]
        Fragment kind searched by default.
    """

    value: Literal["documents", "properties"]

    def __post_init__(self):
        """Validate and capture the control.

        Raises
        ------
        ValueError
            If value is not a valid fragment-scope value.
        """
        if self.value not in ("documents", "properties"):
            message = "fragment-scope must be documents or properties"
            raise ValueError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition("fragment-scope", value=self.value),
        )


@dataclass(frozen=True)
class SearchOptionString(SearchOption):
    """Set search-option.

    Parameters
    ----------
    value : str
        Native cts:search option; compose several instances for multiple options.
    """

    value: str

    def __post_init__(self):
        """Validate and capture the control.

        Raises
        ------
        TypeError
            If value is not a valid search-option value.
        """
        if not isinstance(self.value, str):
            message = "search-option must be a string"
            raise TypeError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition("search-option", value=self.value),
        )


@dataclass(frozen=True)
class _Renamed(QueryComponent):
    """Use a component's contents under a different native name.

    Parameters
    ----------
    name : str
        Destination member name.
    component : QueryComponent
        Immutable source component, serialized only on demand.
    """

    name: str
    component: QueryComponent

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Rename one component in the requested vocabulary.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Native output vocabulary.

        Returns
        -------
        dict or XmlElement
            Independent renamed component.
        """
        if output_format == "json":
            return {self.name: next(iter(self.component.to_json().values()))}
        node = self.component.to_xml()
        node.tag = f"{{{SEARCH_NS_URI}}}{self.name}"
        return node


def _present(values: dict) -> dict:
    """Capture optional attributes, retaining false, zero and empty strings.

    Parameters
    ----------
    values : dict
        Native attribute names and optional values.

    Returns
    -------
    dict
        Attributes whose values are not None.
    """
    return {name: value for name, value in values.items() if value is not None}


def _scalars(values: dict) -> tuple[QueryComponent, ...]:
    """Describe optional scalar children without serializing them.

    Parameters
    ----------
    values : dict
        Native child names and values, with None meaning omitted.

    Returns
    -------
    tuple[QueryComponent, ...]
        Scalar child definitions in input order.
    """
    return tuple(
        _Definition(name, value=value)
        for name, value in values.items()
        if value is not None
    )


@dataclass(frozen=True)
class Callback(_OptionComponent):
    """Identify a Search API extension function.

    Parameters
    ----------
    apply : str
        Function local name or built-in behavior name.
    ns : str | None
        Function namespace URI.
    at : str | None
        Module location in the modules database.
    """

    apply: str
    ns: str | None = None
    at: str | None = None

    def __post_init__(self):
        """Capture the function attributes in an immutable definition."""
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "callback",
                _present({"apply": self.apply, "ns": self.ns, "at": self.at}),
            ),
        )


@dataclass(frozen=True)
class Bucket(_OptionComponent):
    """Define a fixed facet bucket with inclusive lower and exclusive upper bounds.

    Parameters
    ----------
    name : str
        Token used in string queries.
    label : str
        Display label, represented as XML text.
    ge : str | int | float | None
        Inclusive lower bound in the range index's native type.
    lt : str | int | float | None
        Exclusive upper bound.
    """

    name: str
    label: str
    ge: str | int | float | None = None
    lt: str | int | float | None = None

    def __post_init__(self):
        """Capture bounds separately from the display label."""
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "bucket",
                _present(
                    {
                        "name": self.name,
                        "label": self.label,
                        "ge": self.ge,
                        "lt": self.lt,
                    },
                ),
                text_member="label",
            ),
        )


@dataclass(frozen=True)
class ComputedBucket(_OptionComponent):
    """Define a date/time facet bucket relative to an anchor.

    Parameters
    ----------
    name : str
        Query token.
    label : str
        Display label.
    ge : str | None
        Inclusive lower duration offset.
    lt : str | None
        Exclusive upper duration offset.
    anchor : str | None
        Shared anchor, such as start-of-day.
    ge_anchor : str | None
        Lower-bound anchor overriding the shared anchor.
    lt_anchor : str | None
        Upper-bound anchor overriding the shared anchor.
    """

    name: str
    label: str
    ge: str | None = None
    lt: str | None = None
    anchor: str | None = None
    ge_anchor: str | None = None
    lt_anchor: str | None = None

    def __post_init__(self):
        """Capture duration offsets and anchor choices."""
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "computed-bucket",
                _present(
                    {
                        "name": self.name,
                        "label": self.label,
                        "ge": self.ge,
                        "lt": self.lt,
                        "anchor": self.anchor,
                        "ge-anchor": self.ge_anchor,
                        "lt-anchor": self.lt_anchor,
                    },
                ),
                text_member="label",
            ),
        )


@dataclass(frozen=True)
class Heatmap(_OptionComponent):
    """Define a geospatial facet's rectangular grid.

    Parameters
    ----------
    south, west, north, east : float
        Bounding box coordinates in the index coordinate system.
    latitude_divisions, longitude_divisions : int
        Positive grid dimensions.
    """

    south: float
    west: float
    north: float
    east: float
    latitude_divisions: int
    longitude_divisions: int

    def __post_init__(self):
        """Reject non-finite coordinates and invalid grid dimensions.

        Raises
        ------
        ValueError
            If coordinates are non-finite or a division count is not positive.
        """
        for coordinate in (self.south, self.west, self.north, self.east):
            if (
                isinstance(coordinate, bool)
                or not isinstance(coordinate, (int, float))
                or not math.isfinite(coordinate)
            ):
                message = "heatmap coordinates must be finite numbers"
                raise ValueError(message)
        for count in (self.latitude_divisions, self.longitude_divisions):
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                message = "heatmap divisions must be positive integers"
                raise ValueError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "heatmap",
                {
                    "s": self.south,
                    "w": self.west,
                    "n": self.north,
                    "e": self.east,
                    "latdivs": self.latitude_divisions,
                    "londivs": self.longitude_divisions,
                },
            ),
        )


@dataclass(frozen=True)
class Aggregate(_OptionComponent):
    """Request an aggregate from a values or tuples definition.

    Parameters
    ----------
    apply : str
        Built-in aggregate name or native plugin function name.
    udf : str | None
        Native aggregate plugin name, when needed.
    """

    apply: str
    udf: str | None = None

    def __post_init__(self):
        """Capture the aggregate function and optional plugin."""
        object.__setattr__(
            self,
            "_definition",
            _Definition("aggregate", _present({"apply": self.apply, "udf": self.udf})),
        )


@dataclass(frozen=True)
class Word(_OptionComponent):
    """Describe word matching for a constraint, default term or suggestion source.

    Parameters
    ----------
    target : Element | JsonProperty | Field
        Indexed target.
    attribute : Attribute | None
        Attribute of an element target.
    options : str | Sequence[str] | None
        Native term-option strings.
    fragment_scope : {'documents', 'properties'} | None
        Fragment kind matched by this definition.
    weight : float | None
        Relevance weight.
    collation : str | None
        Word lexicon collation used for suggestions.
    """

    target: Element | JsonProperty | Field
    attribute: Attribute | None = None
    options: str | Sequence[str] | None = None
    fragment_scope: Literal["documents", "properties"] | None = None
    weight: float | None = None
    collation: str | None = None

    def __post_init__(self):
        """Validate the target and snapshot option strings.

        Raises
        ------
        TypeError
            If the target or attribute is incompatible.
        """
        _matching(self.fragment_scope, self.weight)
        targets = _term_target("word", self.target, self.attribute)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "word",
                {
                    **_present({"collation": self.collation}),
                    **_option_members("term-option", self.options),
                },
                (
                    *targets,
                    *_scalars(
                        {"fragment-scope": self.fragment_scope, "weight": self.weight},
                    ),
                ),
            ),
        )
        if self.options is not None and not isinstance(self.options, str):
            object.__setattr__(self, "options", tuple(self.options))


@dataclass(frozen=True)
class Value(_OptionComponent):
    """Describe exact-value matching for a constraint or default term.

    Parameters
    ----------
    target : Element | JsonProperty | Field
        Matched target.
    attribute : Attribute | None
        Attribute of an element target.
    node_type : {'string', 'boolean', 'null', 'number'} | None
        JSON node type, with None retaining the server default.
    options : str | Sequence[str] | None
        Native term-option strings.
    fragment_scope : {'documents', 'properties'} | None
        Fragment kind.
    weight : float | None
        Relevance weight.
    """

    target: Element | JsonProperty | Field
    attribute: Attribute | None = None
    node_type: _JsonNodeType | None = None
    options: str | Sequence[str] | None = None
    fragment_scope: Literal["documents", "properties"] | None = None
    weight: float | None = None

    def __post_init__(self):
        """Validate the target and JSON node type before serialization.

        Raises
        ------
        TypeError
            If the target or attribute is incompatible.
        ValueError
            If node_type is not a native JSON node type.
        """
        _matching(self.fragment_scope, self.weight)
        targets = _term_target("value", self.target, self.attribute)
        if self.node_type is not None and self.node_type not in _JSON_NODE_TYPES:
            message = "value node_type must be string, boolean, null or number"
            raise ValueError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "value",
                {
                    **_present({"type": self.node_type}),
                    **_option_members("term-option", self.options),
                },
                (
                    *targets,
                    *_scalars(
                        {"fragment-scope": self.fragment_scope, "weight": self.weight},
                    ),
                ),
            ),
        )
        if self.options is not None and not isinstance(self.options, str):
            object.__setattr__(self, "options", tuple(self.options))


@dataclass(frozen=True)
class Collection(_OptionComponent):
    """Describe collection matching or the collection lexicon.

    Parameters
    ----------
    prefix : str | None
        Collection URI prefix prepended to query tokens.
    facet : bool | None
        Whether to calculate a facet; None retains the native default.
    options : str | Sequence[str] | None
        Native facet-option strings.
    """

    prefix: str | None = None
    facet: bool | None = None
    options: str | Sequence[str] | None = None

    def __post_init__(self):
        """Capture collection settings and snapshot facet options."""
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "collection",
                {
                    **_present({"prefix": self.prefix, "facet": self.facet}),
                    **_option_members("facet-option", self.options),
                },
            ),
        )
        if self.options is not None and not isinstance(self.options, str):
            object.__setattr__(self, "options", tuple(self.options))


@dataclass(frozen=True)
class WordLexicon(_OptionComponent):
    """Select the database word lexicon for suggestions.

    Parameters
    ----------
    collation : str | None
        Enabled word lexicon collation.
    fragment_scope : {'documents', 'properties'} | None
        Fragment kind whose words are suggested.
    """

    collation: str | None = None
    fragment_scope: Literal["documents", "properties"] | None = None

    def __post_init__(self):
        """Capture lexicon selection without checking database configuration.

        Raises
        ------
        ValueError
            If fragment_scope is not documents or properties.
        """
        _matching(self.fragment_scope, None)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "word-lexicon",
                _present({"collation": self.collation}),
                _scalars({"fragment-scope": self.fragment_scope}),
            ),
        )


@dataclass(frozen=True)
class ResultDecorator(SearchOption):
    """Call an extension function for each search result.

    Parameters
    ----------
    callback : Callback
        Result decorator function.
    """

    callback: Callback

    def __post_init__(self):
        """Capture the callback under the result-decorator member.

        Raises
        ------
        TypeError
            If callback is not a Callback.
        """
        _require(self.callback, Callback, "result decorator callback")
        object.__setattr__(
            self,
            "_definition",
            _Renamed("result-decorator", self.callback),
        )


@dataclass(frozen=True)
class PreferredMatches(_OptionComponent):
    """Prefer these elements and JSON properties when creating snippets.

    Parameters
    ----------
    targets : Sequence[Element | JsonProperty]
        Targets in preference order.
    """

    targets: Sequence[Element | JsonProperty]

    def __post_init__(self):
        """Snapshot and validate the preferred targets.

        Raises
        ------
        TypeError
            If a target is not an element or JSON property.
        """
        targets = tuple(self.targets)
        if any(not isinstance(target, (Element, JsonProperty)) for target in targets):
            message = "preferred matches require Element or JsonProperty targets"
            raise TypeError(message)
        object.__setattr__(self, "targets", targets)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "preferred-matches",
                children=targets,
                repeatable=frozenset({"element", "json-property"}),
            ),
        )


@dataclass(frozen=True)
class TransformResults(SearchOption):
    """Choose snippets, raw results or an extension function.

    Parameters
    ----------
    apply : str
        Built-in snippet, metadata-snippet, raw, empty-snippet, or function name.
    ns, at : str | None
        Namespace and module location for a custom function.
    preferred_matches : PreferredMatches | None
        Preferred snippet targets.
    per_match_tokens, max_matches, max_snippet_chars : int | None
        Native snippet size limits.
    parameters : Sequence[QueryComponent]
        Custom extension data, supplied as independent native components.
    """

    apply: str = "snippet"
    ns: str | None = None
    at: str | None = None
    preferred_matches: PreferredMatches | None = None
    per_match_tokens: int | None = None
    max_matches: int | None = None
    max_snippet_chars: int | None = None
    parameters: Sequence[QueryComponent] = ()

    def __post_init__(self):
        """Snapshot custom data and capture the snippet settings.

        Raises
        ------
        TypeError
            If a preferred match group or custom parameter has the wrong type.
        ValueError
            If a snippet limit is not a non-negative integer.
        """
        if self.preferred_matches is not None:
            _require(self.preferred_matches, PreferredMatches, "preferred matches")
        for parameter in self.parameters:
            _require(parameter, QueryComponent, "transform parameter")
        for value in (self.per_match_tokens, self.max_matches, self.max_snippet_chars):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                message = "snippet limits must be non-negative integers"
                raise ValueError(message)
        children = () if self.preferred_matches is None else (self.preferred_matches,)
        object.__setattr__(self, "parameters", tuple(self.parameters))
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "transform-results",
                _present({"apply": self.apply, "ns": self.ns, "at": self.at}),
                (
                    *children,
                    *_scalars(
                        {
                            "per-match-tokens": self.per_match_tokens,
                            "max-matches": self.max_matches,
                            "max-snippet-chars": self.max_snippet_chars,
                        },
                    ),
                    *self.parameters,
                ),
            ),
        )


@dataclass(frozen=True)
class SuggestionSource(SearchOption):
    """Select a constraint or inline lexicon as a suggestion source.

    Parameters
    ----------
    source : Range | Word | Collection | WordLexicon | None
        Optional inline source, also usable as a fallback for ref.
    ref : str | None
        Constraint name; required for SuggestionSource, optional for the default.
    options : str | Sequence[str] | None
        Native suggestion-option strings.
    annotation : str | None
        Source description.
    """

    source: Range | Word | Collection | WordLexicon | None = None
    ref: str | None = None
    options: str | Sequence[str] | None = None

    annotation: str | None = None

    _name: ClassVar[str] = "suggestion-source"

    def __post_init__(self):
        """Validate the inline source and capture suggestion options.

        Raises
        ------
        TypeError
            If the source is not a supported index or lexicon definition.
        """
        if self._name == "suggestion-source" and self.ref is None:
            message = "suggestion-source requires a constraint ref"
            raise ValueError(message)
        if self.source is not None and not isinstance(
            self.source,
            (Range, Word, Collection, WordLexicon),
        ):
            message = "suggestion source must be Range, Word, Collection or WordLexicon"
            raise TypeError(message)
        children = () if self.source is None else (self.source,)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                self._name,
                {
                    **_present({"ref": self.ref}),
                    **_option_members("suggestion-option", self.options),
                },
                (*children, *_scalars({"annotation": self.annotation})),
                repeatable=frozenset({"annotation"}),
            ),
        )
        if self.options is not None and not isinstance(self.options, str):
            object.__setattr__(self, "options", tuple(self.options))


class DefaultSuggestionSource(SuggestionSource):
    """Set the source for unqualified string-query suggestions."""

    _name = "default-suggestion-source"


@dataclass(frozen=True)
class TermDefault(_OptionComponent):
    """Choose matching for unqualified query terms.

    Parameters
    ----------
    source : Word | Value | Range | None
        Inline matching definition.
    ref : str | None
        Constraint name, optionally with an inline fallback.
    annotation : str | None
        Default matching description.
    """

    source: Word | Value | Range | None = None
    ref: str | None = None
    annotation: str | None = None

    def __post_init__(self):
        """Validate and capture the default matching definition.

        Raises
        ------
        TypeError
            If source is not a word, value or range definition.
        """
        if self.source is not None and not isinstance(
            self.source,
            (Word, Value, Range),
        ):
            message = "term default source must be Word, Value or Range"
            raise TypeError(message)
        children = () if self.source is None else (self.source,)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "default",
                _present({"ref": self.ref}),
                (*children, *_scalars({"annotation": self.annotation})),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True)
class Term(SearchOption):
    """Configure unqualified terms, empty queries and custom term parsing.

    Parameters
    ----------
    default : TermDefault | None
        Default term matching.
    empty : str | Callback | None
        Empty-query behavior, usually all-results, no-results or a callback.
    callback : Callback | None
        Custom term parser.
    options : str | Sequence[str] | None
        Native term-option strings.
    fragment_scope : {'documents', 'properties'} | None
        Default fragment kind for terms.
    weight : float | None
        Relevance weight.
    """

    default: TermDefault | None = None
    empty: str | Callback | None = None
    callback: Callback | None = None
    options: str | Sequence[str] | None = None
    fragment_scope: Literal["documents", "properties"] | None = None
    weight: float | None = None

    def __post_init__(self):
        """Capture default and empty-query behavior without invoking callbacks.

        Raises
        ------
        TypeError
            If a default term or parser callback has the wrong type.
        ValueError
            If fragment_scope is unknown or weight is not finite.
        """
        _matching(self.fragment_scope, self.weight)
        if self.default is not None:
            _require(self.default, TermDefault, "default term")
        if self.callback is not None:
            _require(self.callback, Callback, "term callback")
        attributes = (
            {}
            if self.callback is None
            else _present(
                {
                    "apply": self.callback.apply,
                    "ns": self.callback.ns,
                    "at": self.callback.at,
                },
            )
        )
        children = () if self.default is None else (self.default,)
        empty = (
            ()
            if self.empty is None
            else (
                (
                    _Renamed("empty", self.empty)
                    if isinstance(self.empty, Callback)
                    else _Definition("empty", {"apply": self.empty})
                ),
            )
        )
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "term",
                {**attributes, **_option_members("term-option", self.options)},
                (
                    *children,
                    *empty,
                    *_scalars(
                        {"fragment-scope": self.fragment_scope, "weight": self.weight},
                    ),
                ),
            ),
        )
        if self.options is not None and not isinstance(self.options, str):
            object.__setattr__(self, "options", tuple(self.options))


@dataclass(frozen=True)
class AdditionalQuery(SearchOption):
    """AND a native CTS query with every search using these options.

    Parameters
    ----------
    query : SearchQuery
        Serializable CTS query, for example cts.collection_query('published').
        MarkLogic's options JSON represents this as a serialized XML string.
    """

    query: SearchQuery

    @property
    def option_name(self) -> str:
        """Return the additional-query root member name.

        Returns
        -------
        str
            Native root member name.
        """
        return "additional-query"

    def __post_init__(self):
        """Reject objects that do not provide query serialization.

        Raises
        ------
        TypeError
            If query is not a SearchQuery.
        """
        if not isinstance(self.query, SearchQuery):
            message = "additional query must be a serializable CTS SearchQuery"
            raise TypeError(message)

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the CTS child using the options wire contract.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested native format.

        Returns
        -------
        dict or XmlElement
            CTS XML nested in XML, or quoted as text in JSON as required by ML.

        Raises
        ------
        TypeError
            If the query is structured rather than CTS.
        """
        child = self.query.to_xml()
        if not child.tag.startswith("{http://marklogic.com/cts}"):
            message = "additional query requires a CTS query, not a structured query"
            raise TypeError(message)
        if output_format == "json":
            return {"additional-query": tostring(child, encoding="unicode")}
        node = XmlElement(f"{{{SEARCH_NS_URI}}}additional-query")
        node.append(child)
        return node


@dataclass(frozen=True)
class Implicit(_OptionComponent):
    """Choose the implicit CTS operator between unqualified terms.

    Parameters
    ----------
    query : SearchQuery
        Native CTS query such as an empty cts.and_query([]).
    options : str | None
        Lexical CTS constructor options, separated by spaces.
    """

    query: SearchQuery
    options: str | None = None

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize the implicit CTS constructor and optional attributes.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested vocabulary.

        Returns
        -------
        dict or XmlElement
            Native implicit definition, with quoted CTS XML in JSON.
        """
        wrapped = AdditionalQuery(self.query)
        if output_format == "json":
            text = wrapped.to_json()["additional-query"]
            return {
                "implicit": text
                if self.options is None
                else {"text": text, "cts-options": self.options},
            }
        node = wrapped.to_xml()
        node.tag = f"{{{SEARCH_NS_URI}}}implicit"
        if self.options is not None:
            node.set("options", self.options)
        return node


@dataclass(frozen=True)
class Starter(_OptionComponent):
    """Define a string-query grammar prefix operator.

    Parameters
    ----------
    label : str
        Operator token, or an empty string for an implicit starter.
    strength : int
        Operator precedence.
    apply : str
        Native or custom parser function name.
    ns, at : str | None
        Custom parser namespace and module location.
    element : str | None
        CTS query constructor QName.
    options : str | None
        Lexical CTS options.
    delimiter : str | None
        Closing delimiter, such as a right parenthesis.
    tokenize : {'word', 'default'} | None
        Tokenization behavior.
    """

    label: str
    strength: int
    apply: str
    ns: str | None = None
    at: str | None = None
    element: str | None = None
    options: str | None = None
    delimiter: str | None = None
    tokenize: Literal["word", "default"] | None = None

    def __post_init__(self):
        """Capture operator attributes and its token label."""
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "starter",
                _present(
                    {
                        "label": self.label,
                        "strength": self.strength,
                        "apply": self.apply,
                        "ns": self.ns,
                        "at": self.at,
                        "cts-element": self.element,
                        "cts-options": self.options,
                        "delimiter": self.delimiter,
                        "tokenize": self.tokenize,
                    },
                ),
                text_member="label",
            ),
        )


@dataclass(frozen=True)
class Joiner(_OptionComponent):
    """Define a string-query grammar infix operator.

    Parameters
    ----------
    label : str
        Operator token.
    strength : int
        Operator precedence.
    apply : str
        Native or custom parser function.
    ns, at : str | None
        Custom parser namespace and module location.
    element : str | None
        CTS constructor QName.
    options : str | None
        Lexical CTS options.
    compare : str | None
        Comparison operator used by constraint joining.
    consume : int | None
        Number of consumed tokens.
    tokenize : {'word', 'default'} | None
        Tokenization behavior.
    """

    label: str
    strength: int
    apply: str
    ns: str | None = None
    at: str | None = None
    element: str | None = None
    options: str | None = None
    compare: str | None = None
    consume: int | None = None
    tokenize: Literal["word", "default"] | None = None

    def __post_init__(self):
        """Capture the joiner token and native parser attributes."""
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "joiner",
                _present(
                    {
                        "label": self.label,
                        "strength": self.strength,
                        "apply": self.apply,
                        "ns": self.ns,
                        "at": self.at,
                        "cts-element": self.element,
                        "cts-options": self.options,
                        "compare": self.compare,
                        "consume": self.consume,
                        "tokenize": self.tokenize,
                    },
                ),
                text_member="label",
            ),
        )


@dataclass(frozen=True)
class Grammar(SearchOption):
    """Replace the string-query grammar.

    Parameters
    ----------
    quotation : str | None
        Quotation delimiter.
    implicit : Implicit | None
        Implicit CTS joiner.
    starters : Sequence[Starter]
        Prefix operators.
    joiners : Sequence[Joiner]
        Infix operators.
    """

    quotation: str | None = None
    implicit: Implicit | None = None
    starters: Sequence[Starter] = ()
    joiners: Sequence[Joiner] = ()

    def __post_init__(self):
        """Snapshot operators and preserve their array cardinality.

        Raises
        ------
        TypeError
            If an implicit operator, starter or joiner has the wrong type.
        """
        if self.implicit is not None:
            _require(self.implicit, Implicit, "implicit grammar operator")
        for starter in self.starters:
            _require(starter, Starter, "grammar starter")
        for joiner in self.joiners:
            _require(joiner, Joiner, "grammar joiner")
        object.__setattr__(self, "starters", tuple(self.starters))
        object.__setattr__(self, "joiners", tuple(self.joiners))
        implicit = () if self.implicit is None else (self.implicit,)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "grammar",
                children=(
                    *_scalars({"quotation": self.quotation}),
                    *implicit,
                    *self.starters,
                    *self.joiners,
                ),
                repeatable=frozenset({"starter", "joiner"}),
            ),
        )


@dataclass(frozen=True)
class OperatorState(_OptionComponent):
    """Define an operator state that temporarily overrides search options.

    Parameters
    ----------
    name : str
        State token used with the operator name.
    options : SearchOptions
        State-supported options, such as sort-order or page-length.
    """

    name: str
    options: SearchOptions

    def __post_init__(self):
        """Reject options that are unavailable inside an operator state.

        Raises
        ------
        ValueError
            If an option is not part of MarkLogic's state grammar.
        """
        _require(self.options, SearchOptions, "operator state options")
        allowed = {
            "additional-query",
            "debug",
            "forest",
            "page-length",
            "quality-weight",
            "search-option",
            "searchable-expression",
            "sort-order",
            "transform-results",
        }
        for component in self.options.components:
            if component.option_name not in allowed:
                message = (
                    f"{component.option_name} is not supported in an operator state"
                )
                raise ValueError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "state",
                {"name": self.name},
                self.options.components,
                repeatable=_REPEATABLE_MEMBERS,
            ),
        )


@dataclass(frozen=True)
class Operator(SearchOption):
    """Define named states selectable from a string query.

    Parameters
    ----------
    name : str
        Operator name, used as name:state in qtext.
    states : Sequence[OperatorState]
        Named option groups.
    """

    name: str
    states: Sequence[OperatorState]

    def __post_init__(self):
        """Snapshot the state list while preserving its order."""
        for state in self.states:
            _require(state, OperatorState, "operator state")
        object.__setattr__(self, "states", tuple(self.states))
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "operator",
                {"name": self.name},
                self.states,
                repeatable=frozenset({"state"}),
            ),
        )


@dataclass(frozen=True)
class SearchableExpression(SearchOption):
    """Limit searchable nodes with an XPath expression (deprecated by MarkLogic).

    Parameters
    ----------
    path : PathIndex
        XPath and namespace bindings. MarkLogic requires eval-search-string
        privilege; prefer additional-query when possible.
    """

    path: PathIndex

    def __post_init__(self):
        """Reuse the public path component's two native forms."""
        _require(self.path, PathIndex, "searchable expression")
        object.__setattr__(
            self,
            "_definition",
            _Renamed("searchable-expression", self.path),
        )


@dataclass(frozen=True)
class ExtractDocumentData(SearchOption):
    """Extract selected XML paths or JSON property paths into search results.

    Parameters
    ----------
    paths : Sequence[str]
        Absolute extraction paths.
    selected : {'all', 'include', 'include-with-ancestors', 'exclude'} | None
        Extraction selection behavior.
    namespaces : Mapping[str, str] | None
        Prefix bindings shared by the extraction paths.
    """

    paths: Sequence[str] = ()
    selected: Literal["all", "include", "include-with-ancestors", "exclude"] | None = (
        None
    )
    namespaces: Mapping[str, str] | None = None

    def __post_init__(self):
        """Snapshot path strings and namespace bindings.

        Raises
        ------
        ValueError
            If selected is not a native extraction mode.
        """
        if self.selected is not None and self.selected not in (
            "all",
            "include",
            "include-with-ancestors",
            "exclude",
        ):
            message = (
                "extract selected must be all, include, include-with-ancestors or "
                "exclude"
            )
            raise ValueError(message)
        object.__setattr__(self, "paths", tuple(self.paths))
        attributes = {
            **_present({"selected": self.selected}),
            "extract-path": list(self.paths),
        }
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "extract-document-data",
                attributes,
                namespaces=dict(_namespace_bindings(self.namespaces or {})),
            ),
        )
        object.__setattr__(
            self,
            "namespaces",
            _namespace_bindings(self.namespaces or {}),
        )


@dataclass(frozen=True, kw_only=True)
class _Geospatial(_OptionComponent):
    """Shared settings for an existing geospatial index.

    Parameters
    ----------
    options, facet_options : str | Sequence[str] | None
        Native geo-option and facet-option strings.
    fragment_scope : {'documents', 'properties'} | None
        Fragment kind.
    weight : float | None
        Relevance weight.
    heatmap : Heatmap | None
        Optional geospatial facet grid (point indexes only).
    """

    options: str | Sequence[str] | None = None
    facet_options: str | Sequence[str] | None = None
    fragment_scope: Literal["documents", "properties"] | None = None
    weight: float | None = None
    heatmap: Heatmap | None = None

    def _configure(
        self,
        name: str,
        targets: tuple[QueryComponent, ...],
        *,
        coord: str | None = None,
    ):
        """Capture a concrete index's targets and shared settings.

        Parameters
        ----------
        name : str
            Native geospatial member name.
        targets : tuple[QueryComponent, ...]
            Validated index target definitions.
        coord : str | None
            Region index coordinate system.

        Raises
        ------
        ValueError
            If a region index requests point-only faceting.
        """
        _matching(self.fragment_scope, self.weight)
        if self.heatmap is not None:
            _require(self.heatmap, Heatmap, "geospatial heatmap")
        if name == "geo-region-path" and (
            self.heatmap is not None or self.facet_options is not None
        ):
            message = "geo-region-path does not support heatmaps or facet options"
            raise ValueError(message)
        children = (
            *targets,
            *_scalars({"fragment-scope": self.fragment_scope, "weight": self.weight}),
        )
        if self.heatmap is not None:
            children = (*children, self.heatmap)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                name,
                {
                    **_present({"coord": coord}),
                    **_option_members("geo-option", self.options),
                    **_option_members("facet-option", self.facet_options),
                },
                children,
                repeatable=frozenset(
                    target.name
                    for target in targets
                    if sum(other.name == target.name for other in targets) > 1
                ),
            ),
        )
        for member in ("options", "facet_options"):
            value = getattr(self, member)
            if value is not None and not isinstance(value, str):
                object.__setattr__(self, member, tuple(value))


def _geo_targets(
    name: str,
    targets: QueryComponent | Sequence[QueryComponent],
    expected: type,
) -> tuple[QueryComponent, ...]:
    """Validate one or several geospatial index selectors.

    Parameters
    ----------
    name : str
        Native selector member name.
    targets : QueryComponent | Sequence[QueryComponent]
        One selector or a list of selectors.
    expected : type
        Required selector class.

    Returns
    -------
    tuple[QueryComponent, ...]
        Selectors renamed for their geospatial role.

    Raises
    ------
    TypeError
        If any selector has the wrong type.
    """
    items = (targets,) if isinstance(targets, expected) else tuple(targets)
    if not items or any(not isinstance(item, expected) for item in items):
        message = f"{name} requires one or more {expected.__name__} selectors"
        raise TypeError(message)
    return tuple(_Renamed(name, item) for item in items)


@dataclass(frozen=True)
class GeoElement(_Geospatial):
    """Describe an existing geo-elem index.

    Parameters
    ----------
    parent : Element | Sequence[Element]
        Indexed parent selector or selectors.
    element : Element | Sequence[Element]
        Indexed element selector or selectors.
    """

    parent: Element | Sequence[Element]
    element: Element | Sequence[Element]

    def __post_init__(self):
        """Validate and snapshot the index selectors.

        Raises
        ------
        TypeError
            If a selector has an incompatible type.
        """
        targets = ()
        targets += _geo_targets("parent", self.parent, Element)
        if not isinstance(self.parent, Element):
            object.__setattr__(self, "parent", tuple(self.parent))
        targets += _geo_targets("element", self.element, Element)
        if not isinstance(self.element, Element):
            object.__setattr__(self, "element", tuple(self.element))
        self._configure("geo-elem", targets)


@dataclass(frozen=True)
class GeoElementPair(_Geospatial):
    """Describe an existing geo-elem-pair index.

    Parameters
    ----------
    parent : Element | Sequence[Element]
        Indexed parent selector or selectors.
    lat : Element | Sequence[Element]
        Indexed lat selector or selectors.
    lon : Element | Sequence[Element]
        Indexed lon selector or selectors.
    """

    parent: Element | Sequence[Element]
    lat: Element | Sequence[Element]
    lon: Element | Sequence[Element]

    def __post_init__(self):
        """Validate and snapshot the index selectors.

        Raises
        ------
        TypeError
            If a selector has an incompatible type.
        """
        targets = ()
        targets += _geo_targets("parent", self.parent, Element)
        if not isinstance(self.parent, Element):
            object.__setattr__(self, "parent", tuple(self.parent))
        targets += _geo_targets("lat", self.lat, Element)
        if not isinstance(self.lat, Element):
            object.__setattr__(self, "lat", tuple(self.lat))
        targets += _geo_targets("lon", self.lon, Element)
        if not isinstance(self.lon, Element):
            object.__setattr__(self, "lon", tuple(self.lon))
        self._configure("geo-elem-pair", targets)


@dataclass(frozen=True)
class GeoAttributePair(_Geospatial):
    """Describe an existing geo-attr-pair index.

    Parameters
    ----------
    parent : Element | Sequence[Element]
        Indexed parent selector or selectors.
    lat : Attribute | Sequence[Attribute]
        Indexed lat selector or selectors.
    lon : Attribute | Sequence[Attribute]
        Indexed lon selector or selectors.
    """

    parent: Element | Sequence[Element]
    lat: Attribute | Sequence[Attribute]
    lon: Attribute | Sequence[Attribute]

    def __post_init__(self):
        """Validate and snapshot the index selectors.

        Raises
        ------
        TypeError
            If a selector has an incompatible type.
        """
        targets = ()
        targets += _geo_targets("parent", self.parent, Element)
        if not isinstance(self.parent, Element):
            object.__setattr__(self, "parent", tuple(self.parent))
        targets += _geo_targets("lat", self.lat, Attribute)
        if not isinstance(self.lat, Attribute):
            object.__setattr__(self, "lat", tuple(self.lat))
        targets += _geo_targets("lon", self.lon, Attribute)
        if not isinstance(self.lon, Attribute):
            object.__setattr__(self, "lon", tuple(self.lon))
        self._configure("geo-attr-pair", targets)


@dataclass(frozen=True)
class GeoJsonProperty(_Geospatial):
    """Describe an existing geo-json-property index.

    Parameters
    ----------
    parent_property : JsonProperty | Sequence[JsonProperty]
        Indexed parent property selector or selectors.
    json_property : JsonProperty | Sequence[JsonProperty]
        Indexed json property selector or selectors.
    """

    parent_property: JsonProperty | Sequence[JsonProperty]
    json_property: JsonProperty | Sequence[JsonProperty]

    def __post_init__(self):
        """Validate and snapshot the index selectors.

        Raises
        ------
        TypeError
            If a selector has an incompatible type.
        """
        targets = ()
        targets += _geo_targets("parent-property", self.parent_property, JsonProperty)
        if not isinstance(self.parent_property, JsonProperty):
            object.__setattr__(self, "parent_property", tuple(self.parent_property))
        targets += _geo_targets("json-property", self.json_property, JsonProperty)
        if not isinstance(self.json_property, JsonProperty):
            object.__setattr__(self, "json_property", tuple(self.json_property))
        self._configure("geo-json-property", targets)


@dataclass(frozen=True)
class GeoJsonPropertyPair(_Geospatial):
    """Describe an existing geo-json-property-pair index.

    Parameters
    ----------
    parent_property : JsonProperty | Sequence[JsonProperty]
        Indexed parent property selector or selectors.
    lat_property : JsonProperty | Sequence[JsonProperty]
        Indexed lat property selector or selectors.
    lon_property : JsonProperty | Sequence[JsonProperty]
        Indexed lon property selector or selectors.
    """

    parent_property: JsonProperty | Sequence[JsonProperty]
    lat_property: JsonProperty | Sequence[JsonProperty]
    lon_property: JsonProperty | Sequence[JsonProperty]

    def __post_init__(self):
        """Validate and snapshot the index selectors.

        Raises
        ------
        TypeError
            If a selector has an incompatible type.
        """
        targets = ()
        targets += _geo_targets("parent-property", self.parent_property, JsonProperty)
        if not isinstance(self.parent_property, JsonProperty):
            object.__setattr__(self, "parent_property", tuple(self.parent_property))
        targets += _geo_targets("lat-property", self.lat_property, JsonProperty)
        if not isinstance(self.lat_property, JsonProperty):
            object.__setattr__(self, "lat_property", tuple(self.lat_property))
        targets += _geo_targets("lon-property", self.lon_property, JsonProperty)
        if not isinstance(self.lon_property, JsonProperty):
            object.__setattr__(self, "lon_property", tuple(self.lon_property))
        self._configure("geo-json-property-pair", targets)


@dataclass(frozen=True)
class GeoPath(_Geospatial):
    """Describe an existing geo-path index.

    Parameters
    ----------
    path_index : PathIndex | Sequence[PathIndex]
        Indexed path index selector or selectors.
    """

    path_index: PathIndex | Sequence[PathIndex]

    def __post_init__(self):
        """Validate and snapshot the index selectors.

        Raises
        ------
        TypeError
            If a selector has an incompatible type.
        """
        targets = ()
        targets += _geo_targets("path-index", self.path_index, PathIndex)
        if not isinstance(self.path_index, PathIndex):
            object.__setattr__(self, "path_index", tuple(self.path_index))
        self._configure("geo-path", targets)


@dataclass(frozen=True)
class GeoRegionPath(_Geospatial):
    """Describe an existing geo-region-path index.

    Parameters
    ----------
    path_index : PathIndex | Sequence[PathIndex]
        Indexed path index selector or selectors.
    """

    path_index: PathIndex | Sequence[PathIndex]
    coord: str | None = None

    def __post_init__(self):
        """Validate and snapshot the index selectors.

        Raises
        ------
        TypeError
            If a selector has an incompatible type.
        """
        targets = ()
        targets += _geo_targets("path-index", self.path_index, PathIndex)
        if not isinstance(self.path_index, PathIndex):
            object.__setattr__(self, "path_index", tuple(self.path_index))
        self._configure("geo-region-path", targets, coord=self.coord)


@dataclass(frozen=True)
class GeoConstraint(SearchOption):
    """Name a geospatial index for string queries and structured geo constraints.

    Parameters
    ----------
    name : str
        Constraint name.
    index : GeoElement or another geospatial index component
        Existing point or region index and optional geospatial facet settings.
    annotation : str | None
        Constraint description.
    """

    name: str
    index: (
        GeoElement
        | GeoElementPair
        | GeoAttributePair
        | GeoJsonProperty
        | GeoJsonPropertyPair
        | GeoPath
        | GeoRegionPath
    )
    annotation: str | None = None

    def __post_init__(self):
        """Validate the index and name its native definition.

        Raises
        ------
        TypeError
            If index is not a geospatial index definition.
        """
        if not isinstance(self.index, _Geospatial):
            message = "geo constraint index must be a geospatial index definition"
            raise TypeError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "constraint",
                {"name": self.name},
                (self.index, *_scalars({"annotation": self.annotation})),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True)
class PropertiesConstraint(SearchOption):
    """Name a properties-fragment constraint.

    Parameters
    ----------
    name : str
        Constraint name.
    annotation : str | None
        Constraint description.
    """

    name: str
    annotation: str | None = None

    def __post_init__(self):
        """Create the empty properties marker and optional annotation."""
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "constraint",
                {"name": self.name},
                (
                    _Definition("properties", value=None),
                    *_scalars({"annotation": self.annotation}),
                ),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True)
class ElementQueryConstraint(SearchOption):
    """Describe the legacy element-query constraint; prefer ContainerConstraint.

    Parameters
    ----------
    name : str
        Constraint name.
    target : Element
        Container element.
    fragment_scope : {'documents', 'properties'} | None
        Fragment kind.
    annotation : str | None
        Constraint description.
    """

    name: str
    target: Element
    fragment_scope: Literal["documents", "properties"] | None = None
    annotation: str | None = None

    def __post_init__(self):
        """Validate and describe the legacy element constraint.

        Raises
        ------
        TypeError
            If target is not an Element.
        """
        if not isinstance(self.target, Element):
            message = "element-query constraint target must be an Element"
            raise TypeError(message)
        target = _Definition(
            "element-query",
            {"ns": self.target.ns, "name": self.target.name},
            _scalars({"fragment-scope": self.fragment_scope}),
        )
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "constraint",
                {"name": self.name},
                (target, *_scalars({"annotation": self.annotation})),
                repeatable=frozenset({"annotation"}),
            ),
        )


@dataclass(frozen=True)
class CustomConstraint(SearchOption):
    """Define a custom parser and optional custom facet lifecycle.

    Parameters
    ----------
    name : str
        Constraint name.
    parse : Callback
        Custom parse function.
    facet : bool | None
        Whether to calculate a custom facet.
    start_facet, finish_facet : Callback | None
        Facet lifecycle functions.
    facet_options, term_options : str | Sequence[str] | None
        Native facet and term options passed to extension functions.
    annotation : str | None
        Constraint description.
    """

    name: str
    parse: Callback
    facet: bool | None = None
    start_facet: Callback | None = None
    finish_facet: Callback | None = None
    facet_options: str | Sequence[str] | None = None
    term_options: str | Sequence[str] | None = None
    annotation: str | None = None

    def __post_init__(self):
        """Capture callback identities and snapshot extension option strings.

        Raises
        ------
        TypeError
            If a parser or facet callback is not a Callback.
        """
        _require(self.parse, Callback, "custom parse callback")
        for callback in (self.start_facet, self.finish_facet):
            if callback is not None:
                _require(callback, Callback, "custom facet callback")
        callbacks = tuple(
            _Renamed(name, callback)
            for name, callback in (
                ("parse", self.parse),
                ("start-facet", self.start_facet),
                ("finish-facet", self.finish_facet),
            )
            if callback is not None
        )
        custom = _Definition(
            "custom",
            {
                **_present({"facet": self.facet}),
                **_option_members("facet-option", self.facet_options),
                **_option_members("term-option", self.term_options),
            },
            callbacks,
        )
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "constraint",
                {"name": self.name},
                (custom, *_scalars({"annotation": self.annotation})),
                repeatable=frozenset({"annotation"}),
            ),
        )
        for name in ("facet_options", "term_options"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                object.__setattr__(self, name, tuple(value))


@dataclass(frozen=True)
class Anchor(_OptionComponent):
    """Define a named anchor for custom range facets.

    Parameters
    ----------
    name : str
        Anchor name.
    value : str | None
        Fixed anchor value.
    callback : Callback | None
        Function computing the anchor value.
    """

    name: str
    value: str | None = None
    callback: Callback | None = None

    def __post_init__(self):
        """Capture the fixed value or custom anchor function.

        Raises
        ------
        TypeError
            If callback is not a Callback.
        """
        if self.callback is not None:
            _require(self.callback, Callback, "anchor callback")
        attributes = _present({"name": self.name, "value": self.value})
        if self.callback is not None:
            attributes.update(
                _present(
                    {
                        "apply": self.callback.apply,
                        "ns": self.callback.ns,
                        "at": self.callback.at,
                    },
                ),
            )
        object.__setattr__(self, "_definition", _Definition("anchor", attributes))

    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | XmlElement:
        """Serialize a custom anchor in XML only.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested native format.

        Returns
        -------
        XmlElement
            Native anchor definition.

        Raises
        ------
        TypeError
            For JSON, whose server converter cannot preserve anchor elements.
        """
        if output_format == "json":
            message = (
                "custom range anchors require XML; MarkLogic's JSON converter "
                "does not preserve anchor elements"
            )
            raise TypeError(message)
        return super()._serialize(output_format)


@dataclass(frozen=True)
class Annotation(SearchOption):
    """Attach a text annotation to a query-options configuration.

    Parameters
    ----------
    text : str
        Human-readable annotation. Use NativeOptions for arbitrary extension XML.
    """

    text: str

    def __post_init__(self):
        """Capture annotation text without interpreting markup."""
        object.__setattr__(
            self,
            "_definition",
            _Definition("annotation", value=self.text),
        )


@dataclass(frozen=True)
class MetadataQName(_OptionComponent):
    """Identify an XML value to include in extracted metadata.

    Parameters
    ----------
    element : Element
        Metadata element.
    attribute : Attribute | None
        Optional attribute of that element.
    """

    element: Element
    attribute: Attribute | None = None

    def __post_init__(self):
        """Capture the metadata element and optional attribute names.

        Raises
        ------
        TypeError
            If the element or optional attribute has the wrong type.
        """
        _require(self.element, Element, "metadata element")
        if self.attribute is not None:
            _require(self.attribute, Attribute, "metadata attribute")
        attributes = {"elem-ns": self.element.ns, "elem-name": self.element.name}
        if self.attribute is not None:
            attributes.update(
                {"attr-ns": self.attribute.ns, "attr-name": self.attribute.name},
            )
        object.__setattr__(self, "_definition", _Definition("qname", attributes))


@dataclass(frozen=True)
class ConstraintValue(_OptionComponent):
    """Include a constraint value in extracted metadata.

    Parameters
    ----------
    ref : str
        Constraint name.
    """

    ref: str

    def __post_init__(self):
        """Capture the referenced constraint name."""
        object.__setattr__(
            self,
            "_definition",
            _Definition("constraint-value", {"ref": self.ref}),
        )


@dataclass(frozen=True)
class ExtractMetadata(SearchOption):
    """Select metadata values to return with search hits.

    Parameters
    ----------
    sources : Sequence[MetadataQName | JsonProperty | ConstraintValue]
        XML values, JSON properties or named constraints to extract.
    """

    sources: Sequence[MetadataQName | JsonProperty | ConstraintValue]

    def __post_init__(self):
        """Snapshot and validate metadata selectors.

        Raises
        ------
        TypeError
            If a source is not a supported metadata selector.
        """
        sources = tuple(self.sources)
        if any(
            not isinstance(source, (MetadataQName, JsonProperty, ConstraintValue))
            for source in sources
        ):
            message = (
                "metadata sources must be MetadataQName, JsonProperty or "
                "ConstraintValue"
            )
            raise TypeError(message)
        object.__setattr__(self, "sources", sources)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "extract-metadata",
                children=sources,
                repeatable=frozenset({"qname", "json-property", "constraint-value"}),
            ),
        )


def _namespace_bindings(bindings: Mapping[str, str]) -> Mapping[str, str]:
    """Snapshot bindings without permitting protocol namespace rebinding.

    Parameters
    ----------
    bindings : Mapping[str, str]
        Prefix-to-URI mapping.

    Returns
    -------
    Mapping[str, str]
        Read-only independent bindings.

    Raises
    ------
    ValueError
        If a prefix is empty, reserved, or rebinds the native CTS namespace.
    """
    if any(
        prefix in ("", "search", "xml", "xmlns")
        or (prefix == "cts" and uri != "http://marklogic.com/cts")
        for prefix, uri in bindings.items()
    ):
        message = (
            "option namespace prefixes must be non-empty, not reserved, and "
            "preserve cts"
        )
        raise ValueError(message)
    return MappingProxyType(dict(bindings))


def _require(value: object, expected: type | tuple[type, ...], description: str):
    """Validate a required component before it can be serialized.

    Parameters
    ----------
    value : object
        Supplied component.
    expected : type | tuple[type, ...]
        Accepted component classes.
    description : str
        Description included in a type error.

    Raises
    ------
    TypeError
        If value is not an instance of the accepted classes.
    """
    if not isinstance(value, expected):
        message = f"{description} has an incompatible type"
        raise TypeError(message)


def _matching(fragment_scope: str | None, weight: float | None):
    """Validate optional fragment selection and relevance weight.

    Parameters
    ----------
    fragment_scope : str | None
        Native fragment kind.
    weight : float | None
        Relevance weight.

    Raises
    ------
    ValueError
        If the scope is unknown or the weight is not a finite number.
    """
    if fragment_scope is not None and fragment_scope not in ("documents", "properties"):
        message = "fragment scope must be documents or properties"
        raise ValueError(message)
    if weight is not None and (
        isinstance(weight, bool)
        or not isinstance(weight, (int, float))
        or not math.isfinite(weight)
    ):
        message = "weight must be a finite number"
        raise ValueError(message)


def _style(style: str | None):
    """Validate the native values or tuples style.

    Parameters
    ----------
    style : str | None
        Optional native style.

    Raises
    ------
    ValueError
        If style is not default or consistent.
    """
    if style is not None and style not in ("default", "consistent"):
        message = "lexicon style must be default or consistent"
        raise ValueError(message)


def _replace_list_children(node: XmlElement, name: str, values: list[str]):
    """Replace an inherited XML option list with the explicit list.

    Parameters
    ----------
    node : XmlElement
        Fresh parent being serialized.
    name : str
        Native repeated child name.
    values : list[str]
        Explicit option strings in caller order.
    """
    tag = f"{{{SEARCH_NS_URI}}}{name}"
    for previous in list(node):
        if previous.tag == tag:
            node.remove(previous)
    for value in values:
        SubElement(node, tag).text = value
