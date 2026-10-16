"""Build Search API options without installing server configuration."""

from __future__ import annotations

import math
from abc import abstractmethod
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Literal, get_args
from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import SubElement, tostring

from mlclient.search.base import QueryComponent
from mlclient.search.structured import (
    SEARCH_NS_URI,
    Attribute,
    Element,
    Field,
    JsonProperty,
    PathIndex,
)

__all__ = [
    "CollectionConstraint",
    "ContainerConstraint",
    "Control",
    "NativeOption",
    "NativeOptions",
    "PageLength",
    "Range",
    "RangeConstraint",
    "ReturnFacets",
    "SearchOption",
    "SearchOptions",
    "SearchOptionsBuilder",
    "SortOrder",
    "Tuples",
    "ValueConstraint",
    "Values",
    "WordConstraint",
    "opt",
]

# MarkLogic's REST options converter holds these members in JSON arrays
# ($csu:array-element-names in /MarkLogic/rest-api/lib/config-query-util.xqy).
_REPEATABLE_MEMBERS = frozenset(
    {
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
    """

    target: Element | Field | JsonProperty | PathIndex
    index_type: str = "xs:string"
    collation: str | None = None
    attribute: Attribute | None = None

    def __post_init__(self):
        """Reject a target or attribute the range cannot describe.

        Raises
        ------
        TypeError
            For an unsupported target, or an attribute that is not an Attribute
            of an Element target.
        """
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
        members = {"type": self.index_type}
        if self.collation is not None:
            members["collation"] = self.collation
        members.update(self.target.to_json())
        if self.attribute is not None:
            members.update(self.attribute.to_json())
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
        return node


class SearchOption(QueryComponent):
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

    def __init__(self, *options: SearchOption | SearchOptions):
        """Snapshot option composition while retaining immutable components.

        Parameters
        ----------
        *options : SearchOption | SearchOptions
            Individual options or reusable option groups.

        Raises
        ------
        TypeError
            If a component has an unsupported type.
        """
        components = []
        for option in options:
            if isinstance(option, SearchOptions):
                additions = option.components
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
        node.extend(component.to_xml() for component in self.components)
        return node

    def _json(self) -> dict:
        """Build native JSON with arrays for repeatable definitions.

        Returns
        -------
        dict
            Fresh options object.
        """
        members: dict = {}
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
    index: Range | Literal["uri", "collection"]
    options: str | Sequence[str] | None

    def __init__(
        self,
        name: str,
        index: Range | Literal["uri", "collection"],
        *,
        options: str | Sequence[str] | None = None,
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

        Raises
        ------
        TypeError
            For an unsupported index specification.
        """
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "index", index)
        object.__setattr__(
            self,
            "options",
            options if options is None or isinstance(options, str) else tuple(options),
        )
        if not isinstance(index, Range) and index not in ("uri", "collection"):
            message = "values index must be a Range, uri or collection"
            raise TypeError(message)
        target = index if isinstance(index, Range) else _Definition(index, value=None)
        object.__setattr__(
            self,
            "_definition",
            _Definition(
                "values",
                {"name": name, **_option_members("values-option", options)},
                (target,),
            ),
        )


@dataclass(frozen=True, init=False)
class Tuples(SearchOption):
    """Define co-occurring values from two or more existing range indexes."""

    name: str
    indexes: tuple[Range, ...]

    def __init__(self, name: str, *indexes: Range):
        """Define co-occurring values from two or more existing range indexes.

        Parameters
        ----------
        name : str
            Tuples definition name passed to SearchService.tuples or aggregate.
        *indexes : Range
            Two or more range indexes in tuple component order.

        Raises
        ------
        ValueError
            If fewer than two indexes are supplied.
        TypeError
            If an index is not a Range.
        """
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "indexes", indexes)
        if len(indexes) < _MIN_TUPLE_INDEXES:
            message = "tuples requires at least two range indexes"
            raise ValueError(message)
        if any(not isinstance(index, Range) for index in indexes):
            message = "tuples indexes must be Range instances"
            raise TypeError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition("tuples", {"name": name}, indexes),
        )


@dataclass(frozen=True, init=False)
class RangeConstraint(SearchOption):
    """Define a named range constraint and optional facet."""

    name: str
    index: Range
    facet: bool
    options: str | Sequence[str] | None

    def __init__(
        self,
        name: str,
        index: Range,
        *,
        facet: bool = True,
        options: str | Sequence[str] | None = None,
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

        Raises
        ------
        TypeError
            If index is not a Range.
        """
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
                ),
            ),
        )


@dataclass(frozen=True, init=False)
class WordConstraint(SearchOption):
    """Define a named word constraint on an element, JSON property or field."""

    name: str
    target: Element | JsonProperty | Field
    attribute: Attribute | None
    options: str | Sequence[str] | None

    def __init__(
        self,
        name: str,
        target: Element | JsonProperty | Field,
        *,
        attribute: Attribute | None = None,
        options: str | Sequence[str] | None = None,
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

        Raises
        ------
        TypeError
            If target is not an Element, JsonProperty or Field, or attribute is
            not an Attribute of an Element target.
        """
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "attribute", attribute)
        object.__setattr__(
            self,
            "options",
            options if options is None or isinstance(options, str) else tuple(options),
        )
        term = _term_target("word", target, attribute)
        object.__setattr__(
            self,
            "_definition",
            _term_constraint("word", name, term, options),
        )


@dataclass(frozen=True, init=False)
class ValueConstraint(SearchOption):
    """Define a named value constraint on an element, JSON property or field."""

    name: str
    target: Element | JsonProperty | Field
    attribute: Attribute | None
    node_type: _JsonNodeType | None
    options: str | Sequence[str] | None

    def __init__(
        self,
        name: str,
        target: Element | JsonProperty | Field,
        *,
        attribute: Attribute | None = None,
        node_type: _JsonNodeType | None = None,
        options: str | Sequence[str] | None = None,
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

        Raises
        ------
        TypeError
            If target is not an Element, JsonProperty or Field, or attribute is
            not an Attribute of an Element target.
        ValueError
            If node_type is not a JSON node type.
        """
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
        term = _term_target("value", target, attribute)
        object.__setattr__(
            self,
            "_definition",
            _term_constraint("value", name, term, options, node_type=node_type),
        )


@dataclass(frozen=True, init=False)
class CollectionConstraint(SearchOption):
    """Define a named collection constraint and optional facet."""

    name: str
    prefix: str | None
    facet: bool

    def __init__(self, name: str, *, prefix: str | None = None, facet: bool = True):
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
        """
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
                (_Definition("collection", attributes),),
            ),
        )


@dataclass(frozen=True, init=False)
class ContainerConstraint(SearchOption):
    """Define a named container constraint on an element or JSON property."""

    name: str
    target: Element | JsonProperty

    def __init__(self, name: str, target: Element | JsonProperty):
        """Define a named container constraint on an element or JSON property.

        ContainerConstraintQuery names it to match a query within the container.

        Parameters
        ----------
        name : str
            Constraint name.
        target : Element | JsonProperty
            The containing element or JSON property.

        Raises
        ------
        TypeError
            If target is not an Element or JsonProperty.
        """
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
                (_Definition("container", children=(target,)),),
            ),
        )


@dataclass(frozen=True, init=False)
class SortOrder(SearchOption):
    """Append a range-index sort key; keys apply in insertion order."""

    index: Range
    direction: Literal["ascending", "descending"]

    def __init__(
        self,
        index: Range,
        *,
        direction: Literal["ascending", "descending"] = "ascending",
    ):
        """Append a range-index sort key; keys apply in insertion order.

        Parameters
        ----------
        index : Range
            Existing range index.
        direction : {'ascending', 'descending'}, default 'ascending'
            Sort direction.

        Raises
        ------
        TypeError
            If index is not a Range.
        ValueError
            If direction is unsupported.
        """
        object.__setattr__(self, "index", index)
        object.__setattr__(self, "direction", direction)
        if not isinstance(index, Range):
            message = "sort index must be a Range"
            raise TypeError(message)
        if direction not in ("ascending", "descending"):
            message = "sort direction must be ascending or descending"
            raise ValueError(message)
        object.__setattr__(
            self,
            "_definition",
            _Definition("sort-order", {"direction": direction}, index=index),
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
            Native scalar value. Complex options belong in add instead.

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


class SearchOptionsBuilder:
    """Construct immutable options with typed signatures and no mutable state.

    Each factory has the signature of its corresponding option class. Nest
    components in options(), which accepts individual options and reusable
    groups. Range and selector objects describe existing database indexes.
    """

    options = SearchOptions
    range = Range
    values = Values
    tuples = Tuples
    range_constraint = RangeConstraint
    word_constraint = WordConstraint
    value_constraint = ValueConstraint
    collection_constraint = CollectionConstraint
    container_constraint = ContainerConstraint
    sort = SortOrder
    control = Control
    native = NativeOptions
    page_length = PageLength
    return_facets = ReturnFacets


opt = SearchOptionsBuilder()
"""Stateless search-options factories, equivalent to SearchOptionsBuilder()."""


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
    """

    name: str
    attributes: dict = field(default_factory=dict)
    children: tuple[QueryComponent, ...] = ()
    index: Range | None = None
    value: object = ...
    native: tuple[object, XmlElement] | None = None

    def __post_init__(self):
        """Snapshot mutable inputs without serializing nested components."""
        # Targets and ranges are immutable and already snapshot namespace mappings.
        for name in ("attributes", "value", "native"):
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
        for name, value in self.attributes.items():
            if isinstance(value, list):
                continue
            node.set(
                name,
                str(value).lower() if isinstance(value, bool) else str(value),
            )
        if self.value is not ... and self.value is not None:
            node.text = (
                str(self.value).lower()
                if isinstance(self.value, bool)
                else str(self.value)
            )
        node.extend(child.to_xml() for child in self.children)
        for name, values in self.attributes.items():
            if isinstance(values, list):
                for value in values:
                    SubElement(node, f"{{{SEARCH_NS_URI}}}{name}").text = value
        return node

    def _json(self) -> dict:
        """Build this definition and its children as native JSON.

        Returns
        -------
        dict
            One named member; tuple ranges retain their array cardinality.
        """
        if self.value is not ...:
            return {self.name: deepcopy(self.value)}
        members = self.index.to_json()["range"] if self.index is not None else {}
        members.update(deepcopy(self.attributes))
        for child in self.children:
            for name, value in child.to_json().items():
                if self.name == "tuples" and name == "range":
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


def _term_constraint(
    kind: Literal["word", "value"],
    name: str,
    term: tuple[QueryComponent, ...],
    options: str | Sequence[str] | None,
    *,
    node_type: _JsonNodeType | None = None,
) -> _Definition:
    """Describe a word or value constraint with its term options.

    Parameters
    ----------
    kind : {'word', 'value'}
        Native constraint kind.
    name : str
        Constraint name.
    term : tuple[QueryComponent, ...]
        Validated target components, without serialization.
    options : str | Sequence[str] | None
        Native term-option strings.
    node_type : str | None, optional
        JSON value node type; None keeps the native default.

    Returns
    -------
    _Definition
        Immutable native constraint definition.
    """
    attributes = {} if node_type is None else {"type": node_type}
    attributes.update(_option_members("term-option", options))
    return _Definition(
        "constraint",
        {"name": name},
        (_Definition(kind, attributes, term),),
    )
