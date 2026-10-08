"""Build Search API options without installing server configuration."""

from __future__ import annotations

import math
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Literal, get_args
from xml.etree.ElementTree import Element as XmlElement, SubElement, tostring

from mlclient.search.base import QueryComponent
from mlclient.search.structured import (
    SEARCH_NS_URI,
    Attribute,
    Element,
    Field,
    JsonProperty,
    PathIndex,
)

__all__ = ["Range", "SearchOptions"]

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
        attributes = {"type": self.index_type}
        if self.collation is not None:
            attributes["collation"] = self.collation
        targets = [self.target]
        if self.attribute is not None:
            targets.append(self.attribute)
        if output_format == "json":
            for target in targets:
                attributes.update(target.to_json())
            return {"range": attributes}
        node = XmlElement(f"{{{SEARCH_NS_URI}}}range", attributes)
        node.extend([target.to_xml() for target in targets])
        return node


class SearchOptions(QueryComponent):
    """Fluent builder for inline or persistent Search API options.

    Each method adds one definition to this builder and returns it. Every
    definition keeps its input data and components. Only the requested format
    is built when serialize(), to_json() or to_xml() is called. Serialization
    produces independent representations. Options describe indexes; they never
    create them.
    """

    def __init__(self):
        """Create an empty options builder without server interaction."""
        self._definitions: list[_Definition] = []

    def __eq__(self, other: object) -> bool:
        """Compare builders by the options they serialize to.

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

    __hash__ = None

    def __repr__(self) -> str:
        """Name the native definitions in insertion order.

        Returns
        -------
        str
            For example ``SearchOptions(values, page-length)``.
        """
        names = ", ".join(definition.name for definition in self._definitions)
        return f"SearchOptions({names})"

    def values(
        self,
        name: str,
        index: Range | Literal["uri", "collection"],
        *,
        options: str | Sequence[str] | None = None,
    ) -> SearchOptions:
        """Define a named range, URI or collection lexicon.

        Parameters
        ----------
        name : str
            Values definition name passed to SearchService.values or aggregate.
        index : Range | {'uri', 'collection'}
            Existing range index or enabled database lexicon.
        options : str | Sequence[str] | None, default None
            Native values-option strings, such as frequency-order.

        Returns
        -------
        SearchOptions
            This builder.

        Raises
        ------
        TypeError
            For an unsupported index specification.
        """
        if not isinstance(index, Range) and index not in ("uri", "collection"):
            message = "values index must be a Range, uri or collection"
            raise TypeError(message)
        target = index if isinstance(index, Range) else _Definition(index, value=None)
        return self._append(
            _Definition(
                "values",
                {"name": name, **_option_members("values-option", options)},
                (target,),
            ),
        )

    def tuples(self, name: str, *indexes: Range) -> SearchOptions:
        """Define co-occurring values from two or more existing range indexes.

        Parameters
        ----------
        name : str
            Tuples definition name passed to SearchService.tuples or aggregate.
        *indexes : Range
            Two or more range indexes in tuple component order.

        Returns
        -------
        SearchOptions
            This builder.

        Raises
        ------
        ValueError
            If fewer than two indexes are supplied.
        TypeError
            If an index is not a Range.
        """
        if len(indexes) < _MIN_TUPLE_INDEXES:
            message = "tuples requires at least two range indexes"
            raise ValueError(message)
        if any(not isinstance(index, Range) for index in indexes):
            message = "tuples indexes must be Range instances"
            raise TypeError(message)
        return self._append(_Definition("tuples", {"name": name}, indexes))

    def range_constraint(
        self,
        name: str,
        index: Range,
        *,
        facet: bool = True,
        options: str | Sequence[str] | None = None,
    ) -> SearchOptions:
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

        Returns
        -------
        SearchOptions
            This builder.

        Raises
        ------
        TypeError
            If index is not a Range.
        """
        if not isinstance(index, Range):
            message = "range constraint index must be a Range"
            raise TypeError(message)
        return self._append(
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

    def word_constraint(
        self,
        name: str,
        target: Element | JsonProperty | Field,
        *,
        attribute: Attribute | None = None,
        options: str | Sequence[str] | None = None,
    ) -> SearchOptions:
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

        Returns
        -------
        SearchOptions
            This builder.

        Raises
        ------
        TypeError
            If target is not an Element, JsonProperty or Field, or attribute is
            not an Attribute of an Element target.
        """
        term = _term_target("word", target, attribute)
        return self._term_constraint("word", name, term, options)

    def value_constraint(
        self,
        name: str,
        target: Element | JsonProperty | Field,
        *,
        attribute: Attribute | None = None,
        node_type: _JsonNodeType | None = None,
        options: str | Sequence[str] | None = None,
    ) -> SearchOptions:
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

        Returns
        -------
        SearchOptions
            This builder.

        Raises
        ------
        TypeError
            If target is not an Element, JsonProperty or Field, or attribute is
            not an Attribute of an Element target.
        ValueError
            If node_type is not a JSON node type.
        """
        if node_type is not None and node_type not in _JSON_NODE_TYPES:
            message = (
                f"value constraint node_type must be one of "
                f"{', '.join(sorted(_JSON_NODE_TYPES))}, got {node_type!r}"
            )
            raise ValueError(message)
        term = _term_target("value", target, attribute)
        return self._term_constraint("value", name, term, options, node_type=node_type)

    def collection_constraint(
        self,
        name: str,
        *,
        prefix: str | None = None,
        facet: bool = True,
    ) -> SearchOptions:
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

        Returns
        -------
        SearchOptions
            This builder.
        """
        attributes = {"facet": facet}
        if prefix is not None:
            attributes["prefix"] = prefix
        return self._append(
            _Definition(
                "constraint",
                {"name": name},
                (_Definition("collection", attributes),),
            ),
        )

    def container_constraint(
        self,
        name: str,
        target: Element | JsonProperty,
    ) -> SearchOptions:
        """Define a named container constraint on an element or JSON property.

        ContainerConstraintQuery names it to match a query within the container.

        Parameters
        ----------
        name : str
            Constraint name.
        target : Element | JsonProperty
            The containing element or JSON property.

        Returns
        -------
        SearchOptions
            This builder.

        Raises
        ------
        TypeError
            If target is not an Element or JsonProperty.
        """
        if not isinstance(target, (Element, JsonProperty)):
            message = "container constraint target must be an Element or JsonProperty"
            raise TypeError(message)
        return self._append(
            _Definition(
                "constraint",
                {"name": name},
                (_Definition("container", children=(target,)),),
            ),
        )

    def sort(
        self,
        index: Range,
        *,
        direction: Literal["ascending", "descending"] = "ascending",
    ) -> SearchOptions:
        """Append a range-index sort key; keys apply in insertion order.

        Parameters
        ----------
        index : Range
            Existing range index.
        direction : {'ascending', 'descending'}, default 'ascending'
            Sort direction.

        Returns
        -------
        SearchOptions
            This builder.

        Raises
        ------
        TypeError
            If index is not a Range.
        ValueError
            If direction is unsupported.
        """
        if not isinstance(index, Range):
            message = "sort index must be a Range"
            raise TypeError(message)
        if direction not in ("ascending", "descending"):
            message = "sort direction must be ascending or descending"
            raise ValueError(message)
        return self._append(
            _Definition(
                "sort-order",
                {"direction": direction},
                index=index,
            ),
        )

    def control(self, name: str, value: str | int | float | bool) -> SearchOptions:
        """Set a scalar top-level option such as page-length or return-facets.

        A repeatable option such as search-option accumulates; any other
        replaces an earlier value.

        Parameters
        ----------
        name : str
            Native Search API scalar option name, including hyphens.
        value : str | int | float | bool
            Native scalar value. Complex options belong in add instead.

        Returns
        -------
        SearchOptions
            This builder.

        Raises
        ------
        TypeError
            If value is not a string, number or boolean.
        ValueError
            If a float value is not finite.
        """
        if not isinstance(value, (str, int, float, bool)):
            message = "control value must be a string, number or boolean"
            raise TypeError(message)
        if isinstance(value, float) and not math.isfinite(value):
            message = "control value must be finite"
            raise ValueError(message)
        return self._append(_Definition(name, value=value))

    def add(self, definition: dict, *elements: XmlElement) -> SearchOptions:
        """Add native options members that have no convenience method.

        Supply every member in both native forms: each JSON definition needs
        one search-namespace XML element with the member's name, because
        neither representation is converted through the other.

        Parameters
        ----------
        definition : dict
            Native JSON options members, without the outer options wrapper. A
            list member holds one definition per item and appends to earlier
            definitions; any other member is one definition that replaces an
            earlier one of the same name.
        *elements : xml.etree.ElementTree.Element
            The same definitions as search-namespace XML children, matched to
            JSON items by name and order. Serialization follows the JSON order.

        Returns
        -------
        SearchOptions
            This builder, holding defensive copies of the definitions.

        Raises
        ------
        ValueError
            If an element is outside the search namespace, or a member does not
            have exactly as many XML elements as JSON definitions.
        """
        for added in _pair_native_definitions(definition, elements):
            self._append(added)
        return self

    def _term_constraint(
        self,
        kind: Literal["word", "value"],
        name: str,
        term: tuple[QueryComponent, ...],
        options: str | Sequence[str] | None,
        *,
        node_type: _JsonNodeType | None = None,
    ) -> SearchOptions:
        """Add a word or value constraint with its term options.

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
        SearchOptions
            This builder.
        """
        attributes = {} if node_type is None else {"type": node_type}
        attributes.update(_option_members("term-option", options))
        return self._append(
            _Definition(
                "constraint",
                {"name": name},
                (
                    _Definition(
                        kind,
                        attributes,
                        term,
                    ),
                ),
            ),
        )

    def _append(self, definition: _Definition) -> SearchOptions:
        """Add one definition, replacing an earlier non-repeatable namesake.

        Parameters
        ----------
        definition : _Definition
            Input data and components for one native definition.

        Returns
        -------
        SearchOptions
            This builder.
        """
        if not definition.repeatable:
            self._definitions = [
                held for held in self._definitions if held.name != definition.name
            ]
        self._definitions.append(definition)
        return self

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
        if output_format == "xml":
            node = XmlElement(f"{{{SEARCH_NS_URI}}}options")
            node.extend([held.to_xml() for held in self._definitions])
            return node
        members: dict = {}
        for held in self._definitions:
            definition = held.to_json()[held.name]
            if held.repeatable:
                members.setdefault(held.name, []).append(definition)
            else:
                members[held.name] = definition
        return {"options": members}


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
        Caller-supplied native forms from add(); no format conversion is performed.
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
                name, str(value).lower() if isinstance(value, bool) else str(value),
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

    @property
    def repeatable(self) -> bool:
        """Whether definitions of this name accumulate rather than replace.

        Returns
        -------
        bool
            True for the members native JSON holds in an array.
        """
        return self.name in _REPEATABLE_MEMBERS


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
                f"add requires XML elements in the {SEARCH_NS_URI} namespace; "
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
                "add requires one search-namespace XML element per JSON "
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
