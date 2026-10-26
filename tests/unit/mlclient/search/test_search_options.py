"""Model validation, immutable composition and complete native options payloads.

Each serialization resource covers one option inside SearchOptions, except cases
specifically checking accumulation or replacement. Constructor aliases belong
in test_opt.py; component behavior is checked directly when composition is irrelevant.
"""

from dataclasses import FrozenInstanceError
from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import fromstring, tostring

import pytest

from mlclient.search import options
from mlclient.search.options import (
    ContainerConstraint,
    Control,
    NativeOption,
    NativeOptions,
    PageLength,
    Range,
    RangeConstraint,
    ReturnFacets,
    SearchOptions,
    SortOrder,
    Tuples,
    ValueConstraint,
    Values,
    WordConstraint,
)
from mlclient.search.structured import (
    Attribute,
    Element,
    Field,
    JsonProperty,
    PathIndex,
    TermQuery,
)
from mlclient.xquery import cts
from tests.utils.resources import discover_serialization_cases

SEARCH_NAMESPACE = "http://marklogic.com/appservices/search"


def test_typed_constraint_survives_a_later_native_constraint():
    element = XmlElement(f"{{{SEARCH_NAMESPACE}}}constraint", {"name": "a"})
    options = SearchOptions(
        WordConstraint("b", Element("b")),
        NativeOptions({"constraint": {"name": "a"}}, element),
    )
    assert [c["name"] for c in options.to_json()["options"]["constraint"]] == ["b", "a"]


def test_search_options_are_not_equal_to_their_serialization():
    options = SearchOptions(Control("page-length", 5))
    assert options != options.to_json()


PRICE_RANGE = Range(Element("price"), "xs:decimal")


def test_search_options_with_the_same_definitions_are_equal():
    assert SearchOptions(
        Values("price", PRICE_RANGE),
        Control("page-length", 5),
    ) == SearchOptions(Values("price", PRICE_RANGE), Control("page-length", 5))
    assert SearchOptions(Values("price", PRICE_RANGE)) != SearchOptions(
        SortOrder(PRICE_RANGE),
    )


@pytest.mark.parametrize(
    ("target", "attribute"),
    [(JsonProperty("item"), Attribute("code")), (Element("item"), Element("code"))],
)
def test_search_options_constraint_attribute_requires_an_element_and_an_attribute(
    target,
    attribute,
):
    with pytest.raises(TypeError) as error:
        SearchOptions(ValueConstraint("code", target, attribute=attribute))
    assert str(error.value) == (
        "value constraint attribute requires an Element target and an Attribute"
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_search_options_control_rejects_a_non_finite_float(value):
    with pytest.raises(ValueError, match="must be finite") as error:
        SearchOptions(Control("quality-weight", value))
    assert str(error.value) == "control value must be finite"


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (
            lambda: SearchOptions(WordConstraint("label", "label")),
            ("word constraint target must be an Element, JsonProperty or Field"),
        ),
        (
            lambda: SearchOptions(ValueConstraint("label", None)),
            ("value constraint target must be an Element, JsonProperty or Field"),
        ),
        (
            lambda: SearchOptions(ContainerConstraint("place", Field("place"))),
            "container constraint target must be an Element or JsonProperty",
        ),
    ],
)
def test_search_options_invalid_constraint_targets(build, message):
    with pytest.raises(TypeError) as error:
        build()
    assert str(error.value) == message


def test_search_options_native_options_are_copied():
    definition = {"transform-results": {"apply": "empty-snippet"}}
    element = XmlElement(
        f"{{{SEARCH_NAMESPACE}}}transform-results",
        {"apply": "empty-snippet"},
    )
    options = SearchOptions(NativeOptions(definition, element))
    definition["transform-results"]["apply"] = "raw"
    element.set("apply", "raw")
    assert options.to_json() == {
        "options": {"transform-results": {"apply": "empty-snippet"}},
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        '<search:options xmlns:search="http://marklogic.com/apps'
        'ervices/search"><search:transform-results apply="empty-'
        'snippet" /></search:options>'
    )


@pytest.mark.parametrize(
    ("build", "member", "option_name"),
    [
        (
            lambda values: SearchOptions(
                Values("price", PRICE_RANGE, options=values),
            ),
            "values",
            "values-option",
        ),
        (
            lambda values: SearchOptions(
                RangeConstraint("price", PRICE_RANGE, options=values),
            ),
            "range",
            "facet-option",
        ),
        (
            lambda values: SearchOptions(
                WordConstraint("price", Element("price"), options=values),
            ),
            "word",
            "term-option",
        ),
        (
            lambda values: SearchOptions(
                ValueConstraint("price", Element("price"), options=values),
            ),
            "value",
            "term-option",
        ),
    ],
)
def test_search_options_option_lists_are_snapshotted_before_serialization(
    build,
    member,
    option_name,
):
    values = ["first"]
    options = build(values)
    values.append("later")
    result = options.to_json()["options"]
    definition = (
        result["values"][0] if member == "values" else result["constraint"][0][member]
    )
    assert definition[option_name] == ["first"]
    definition[option_name].append("changed output")
    assert "changed output" not in str(options.to_json())
    xml = tostring(options.to_xml(), encoding="unicode")
    assert "first" in xml
    assert "later" not in xml
    assert "changed output" not in xml
    empty = build([]).to_json()["options"]
    definition = (
        empty["values"][0] if member == "values" else empty["constraint"][0][member]
    )
    assert definition[option_name] == []


@pytest.mark.parametrize(
    "build",
    [
        lambda index: SearchOptions(Values("price", index)),
        lambda index: SearchOptions(Tuples("pair", index, index)),
        lambda index: SearchOptions(RangeConstraint("price", index)),
        lambda index: SearchOptions(SortOrder(index)),
    ],
)
def test_search_options_path_namespaces_remain_snapshotted_and_serializable(build):
    namespaces = {"p": "https://example.com/prices"}
    index = Range(PathIndex("/p:price", namespaces), "xs:decimal")
    options = build(index)
    namespaces["p"] = "https://example.com/changed"
    assert "https://example.com/prices" in str(options.to_json())
    assert "https://example.com/changed" not in str(options.to_json())
    xml = tostring(options.to_xml(), encoding="unicode")
    assert "https://example.com/prices" in xml
    assert "https://example.com/changed" not in xml


@pytest.mark.parametrize(
    "build",
    [
        lambda index: SearchOptions(Values("price", index)),
        lambda index: SearchOptions(Tuples("pair", index, index)),
        lambda index: SearchOptions(RangeConstraint("price", index)),
        lambda index: SearchOptions(SortOrder(index)),
    ],
    ids=["values", "tuples", "range-constraint", "sort"],
)
def test_search_options_range_components_serialize_only_when_requested(build):
    calls = []

    class RecordingRange(Range):
        def to_json(self):
            calls.append("json")
            return super().to_json()

        def to_xml(self):
            calls.append("xml")
            return super().to_xml()

    options = build(RecordingRange(Element("price"), "xs:decimal"))
    assert calls == []
    options.to_json()
    assert calls
    assert set(calls) == {"json"}
    calls.clear()
    options.to_xml()
    assert calls
    assert set(calls) == {"xml"}


def test_search_options_repr_names_the_definitions():
    options = SearchOptions(
        Values("price", PRICE_RANGE),
        Control("page-length", 5),
    )
    assert repr(options) == "SearchOptions(values, page-length)"


def test_search_options_serialization_is_defensive():
    options = SearchOptions(Values("price", PRICE_RANGE))
    options.to_json()["options"]["values"].clear()
    options.to_xml().clear()
    assert options.to_json() == {
        "options": {
            "values": [
                {
                    "name": "price",
                    "range": {
                        "type": "xs:decimal",
                        "element": {"name": "price", "ns": ""},
                    },
                },
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        '<search:options xmlns:search="http://marklogic.com/apps'
        'ervices/search"><search:values name="price"><search:ran'
        'ge type="xs:decimal"><search:element name="price" ns=""'
        " /></search:range></search:values></search:options>"
    )


def test_search_options_single_native_constraint_and_typed_constraints_accumulate():
    element = XmlElement(f"{{{SEARCH_NAMESPACE}}}constraint", {"name": "a"})
    options = SearchOptions(
        NativeOptions({"constraint": {"name": "a"}}, element),
        WordConstraint("b", Element("b")),
    )
    assert [c["name"] for c in options.to_json()["options"]["constraint"]] == ["a", "b"]
    assert [c.get("name") for c in options.to_xml()] == ["a", "b"]


@pytest.mark.parametrize(
    "build",
    [
        lambda target: SearchOptions(WordConstraint("label", target)),
        lambda target: SearchOptions(ValueConstraint("label", target)),
        lambda target: SearchOptions(ContainerConstraint("label", target)),
    ],
    ids=["word-constraint", "value-constraint", "container-constraint"],
)
def test_search_options_target_components_serialize_only_when_requested(build):
    calls = []

    class RecordingElement(Element):
        def to_json(self):
            calls.append("json")
            return super().to_json()

        def to_xml(self):
            calls.append("xml")
            return super().to_xml()

    options = build(RecordingElement("label"))
    assert calls == []
    options.to_json()
    assert calls == ["json"]
    calls.clear()
    options.to_xml()
    assert calls == ["xml"]


def test_options_components_can_be_reused_without_mutating_original_groups():
    constraint = WordConstraint("title", Element("title"))
    defaults = SearchOptions(constraint, PageLength(10))
    paged = SearchOptions(defaults, PageLength(20), ReturnFacets(False))

    assert defaults.to_json() == {
        "options": {
            "constraint": [
                {"name": "title", "word": {"element": {"name": "title", "ns": ""}}},
            ],
            "page-length": 10,
        },
    }
    assert paged.to_json() == {
        "options": {
            "constraint": [
                {"name": "title", "word": {"element": {"name": "title", "ns": ""}}},
            ],
            "page-length": 20,
            "return-facets": False,
        },
    }
    assert tostring(paged.to_xml(), encoding="unicode") == (
        '<search:options xmlns:search="http://marklogic.com/appservices/search">'
        '<search:constraint name="title"><search:word><search:element name="title" '
        'ns="" /></search:word></search:constraint><search:page-length>20'
        "</search:page-length><search:return-facets>false</search:return-facets>"
        "</search:options>"
    )


def test_option_components_are_immutable_and_snapshot_option_lists():
    terms = ["unstemmed"]
    constraint = WordConstraint("title", Element("title"), options=terms)
    terms.append("case-sensitive")
    assert constraint.options == ("unstemmed",)
    with pytest.raises(FrozenInstanceError) as error:
        constraint.name = "changed"
    assert str(error.value) == "cannot assign to field 'name'"


@pytest.mark.parametrize("value", [True, 1.5, "20"])
def test_page_length_rejects_non_integer_values(value):
    with pytest.raises(TypeError) as error:
        PageLength(value)
    assert str(error.value) == "page length must be an integer"


@pytest.mark.parametrize("value", [0, -1])
def test_page_length_requires_a_positive_value(value):
    with pytest.raises(ValueError, match="page length must be positive") as error:
        PageLength(value)
    assert str(error.value) == "page length must be positive"


@pytest.mark.parametrize("value", [0, "false", None])
def test_return_facets_requires_a_boolean(value):
    with pytest.raises(TypeError) as error:
        ReturnFacets(value)
    assert str(error.value) == "return facets must be a boolean"


def test_options_rejects_non_option_components():
    with pytest.raises(TypeError) as error:
        SearchOptions({"page-length": 20})
    assert str(error.value) == (
        "options components must be SearchOption or SearchOptions instances"
    )


def test_native_option_equality_compares_json_and_xml_independently():
    element = XmlElement(f"{{{SEARCH_NAMESPACE}}}return-metrics")
    element.text = "false"
    original = NativeOption({"return-metrics": False}, element)
    equivalent = NativeOption({"return-metrics": False}, element)
    element.text = "true"
    different_xml = NativeOption({"return-metrics": False}, element)

    assert original == equivalent
    assert original != different_xml
    assert original != {"return-metrics": False}
    assert original.to_xml().text == "false"


@pytest.mark.parametrize(
    "case",
    discover_serialization_cases(__file__),
    ids=lambda case: case.name,
)
def test_serialization(case):
    case.assert_matches()


def test_return_facets_true_serializes_to_json_and_xml():
    option = ReturnFacets(True)
    assert option.to_json() == {"return-facets": True}
    assert tostring(option.to_xml(), encoding="unicode") == (
        '<search:return-facets xmlns:search="http://marklogic.com/appservices/search">'
        "true</search:return-facets>"
    )


@pytest.mark.parametrize(
    ("constructor", "value", "error_type", "message"),
    [
        (options.Debug, 1, TypeError, "debug must be a boolean"),
        (
            options.ConcurrencyLevel,
            0,
            ValueError,
            "concurrency-level must be a positive integer",
        ),
        (
            options.ConcurrencyLevel,
            True,
            ValueError,
            "concurrency-level must be a positive integer",
        ),
        (
            options.QualityWeight,
            float("inf"),
            ValueError,
            "quality-weight must be a finite number",
        ),
        (
            options.QualityWeight,
            False,
            ValueError,
            "quality-weight must be a finite number",
        ),
        (options.Forest, True, TypeError, "forest must be a string or integer ID"),
        (
            options.FragmentScope,
            "all",
            ValueError,
            "fragment-scope must be documents or properties",
        ),
        (options.SearchOptionString, [], TypeError, "search-option must be a string"),
    ],
)
def test_scalar_controls_reject_invalid_values(constructor, value, error_type, message):
    with pytest.raises(error_type) as error:
        constructor(value)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (
            lambda: options.Word(Element("title"), fragment_scope="all"),
            "fragment scope must be documents or properties",
        ),
        (
            lambda: options.Value(Element("title"), weight=float("nan")),
            "weight must be a finite number",
        ),
        (
            lambda: options.Value(JsonProperty("flag"), node_type="integer"),
            "value node_type must be string, boolean, null or number",
        ),
        (
            lambda: options.Heatmap(float("inf"), 0, 1, 1, 2, 2),
            "heatmap coordinates must be finite numbers",
        ),
        (
            lambda: options.Heatmap(0, 0, 1, 1, 0, 2),
            "heatmap divisions must be positive integers",
        ),
        (
            lambda: options.GeoRegionPath(
                PathIndex("/region"),
                heatmap=options.Heatmap(0, 0, 1, 1, 2, 2),
            ),
            "geo-region-path does not support heatmaps or facet options",
        ),
        (
            lambda: options.OperatorState("short", SearchOptions(ReturnFacets(False))),
            "return-facets is not supported in an operator state",
        ),
        (
            lambda: options.ExtractDocumentData(selected="other"),
            "extract selected must be all, include, include-with-ancestors or exclude",
        ),
        (
            lambda: options.Values("price", Range(Element("price")), style="other"),
            "lexicon style must be default or consistent",
        ),
        (
            lambda: options.TransformResults(max_matches=-1),
            "snippet limits must be non-negative integers",
        ),
        (
            lambda: SearchOptions(namespaces={"search": "https://example.com/wrong"}),
            "option namespace prefixes must be non-empty, "
            "not reserved, and preserve cts",
        ),
    ],
)
def test_option_components_reject_invalid_native_settings(build, message):
    with pytest.raises(ValueError, match=r".") as error:
        build()
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (
            lambda: options.PreferredMatches([Field("title")]),
            "preferred matches require Element or JsonProperty targets",
        ),
        (
            lambda: options.SuggestionSource(
                ValueConstraint("title", Element("title")),
                ref="title",
            ),
            "suggestion source must be Range, Word, Collection or WordLexicon",
        ),
        (
            lambda: options.TermDefault(Element("title")),
            "term default source must be Word, Value or Range",
        ),
        (
            lambda: options.AdditionalQuery({}),
            "additional query must be a serializable CTS SearchQuery",
        ),
        (
            lambda: options.GeoConstraint("place", Range(Element("place"))),
            "geo constraint index must be a geospatial index definition",
        ),
        (
            lambda: options.GeoElement(Element("p"), [Attribute("point")]),
            "element requires one or more Element selectors",
        ),
        (
            lambda: options.ElementQueryConstraint("body", JsonProperty("body")),
            "element-query constraint target must be an Element",
        ),
        (
            lambda: options.ExtractMetadata([Element("title")]),
            "metadata sources must be MetadataQName, JsonProperty or ConstraintValue",
        ),
        (
            lambda: Range(Element("price"), buckets=["low"]),
            "range bucket has an incompatible type",
        ),
        (
            lambda: options.ResultDecorator("decorate"),
            "result decorator callback has an incompatible type",
        ),
        (
            lambda: options.Term(default=Element("title")),
            "default term has an incompatible type",
        ),
        (
            lambda: options.Grammar(starters=["AND"]),
            "grammar starter has an incompatible type",
        ),
        (
            lambda: options.CustomConstraint("custom", None),
            "custom parse callback has an incompatible type",
        ),
    ],
)
def test_option_components_reject_incompatible_components(build, message):
    with pytest.raises(TypeError) as error:
        build()
    assert str(error.value) == message


def test_nullable_range_preserves_xml_and_rejects_lossy_json_conversion():
    index = Range(JsonProperty("price"), "xs:decimal", nullable=True)
    assert tostring(index.to_xml(), encoding="unicode") == (
        '<search:range xmlns:search="http://marklogic.com/appservices/search" '
        'type="xs:decimal" nullable="true"><search:json-property>price'
        "</search:json-property></search:range>"
    )
    with pytest.raises(TypeError) as error:
        index.to_json()
    assert str(error.value) == (
        "nullable range options require XML; "
        "MarkLogic's JSON converter does not preserve nullable"
    )


def test_custom_anchors_preserve_xml_and_reject_lossy_json_conversion():
    index = Range(
        Element("created"),
        "xs:date",
        anchors=[
            options.Anchor(
                "today",
                callback=options.Callback(
                    "today",
                    "https://example.com/search",
                    "/search.xqy",
                ),
            ),
            options.Anchor("fixed", value="2026-01-01"),
        ],
    )
    assert tostring(index.to_xml(), encoding="unicode") == (
        '<search:range xmlns:search="http://marklogic.com/appservices/search" '
        'type="xs:date">'
        '<search:element name="created" ns="" />'
        '<search:anchor name="today" apply="today" '
        'ns="https://example.com/search" at="/search.xqy" />'
        '<search:anchor name="fixed" value="2026-01-01" /></search:range>'
    )
    with pytest.raises(TypeError) as error:
        index.to_json()
    assert str(error.value) == (
        "custom range anchors require XML; "
        "MarkLogic's JSON converter does not preserve anchor elements"
    )


def test_additional_query_rejects_structured_queries():
    option = options.AdditionalQuery(TermQuery("coffee"))
    with pytest.raises(TypeError) as error:
        option.to_json()
    assert (
        str(error.value)
        == "additional query requires a CTS query, not a structured query"
    )


def test_option_groups_merge_and_snapshot_namespace_bindings():
    bindings = {"d": "https://example.com/docs"}
    base = SearchOptions(PageLength(10), namespaces=bindings)
    combined = SearchOptions(base, namespaces={"e": "https://example.com/extra"})
    bindings["d"] = "https://example.com/changed"
    expected = {
        "options": {
            "namespaces": {
                "d": "https://example.com/docs",
                "e": "https://example.com/extra",
            },
            "page-length": 10,
        },
    }
    assert combined.to_json() == expected
    assert tostring(combined.to_xml(), encoding="unicode") == (
        '<search:options xmlns:search="http://marklogic.com/appservices/search" '
        'xmlns:d="https://example.com/docs" xmlns:e="https://example.com/extra">'
        "<search:page-length>10</search:page-length></search:options>"
    )
    combined.to_json()["options"]["namespaces"]["d"] = "changed"
    assert combined.to_json() == expected
    with pytest.raises(TypeError) as error:
        combined.namespaces["d"] = "changed"
    assert str(error.value) == "'mappingproxy' object does not support item assignment"


def test_cts_namespace_is_declared_once_when_options_also_contain_a_cts_query():
    composed = SearchOptions(
        options.AdditionalQuery(cts.true_query()),
        namespaces={"cts": "http://marklogic.com/cts"},
    )
    xml = tostring(composed.to_xml(), encoding="unicode")
    assert xml.count('xmlns:cts="http://marklogic.com/cts"') == 1
    assert fromstring(xml).find(".//{http://marklogic.com/cts}true-query") is not None


@pytest.mark.parametrize(
    ("build", "member", "expected"),
    [
        (
            lambda a, b: options.GeoElementPair(a, b, b),
            "geo-elem-pair",
            {
                "parent": [{"name": "a", "ns": ""}, {"name": "b", "ns": ""}],
                "lat": [{"name": "a", "ns": ""}, {"name": "b", "ns": ""}],
                "lon": [{"name": "a", "ns": ""}, {"name": "b", "ns": ""}],
            },
        ),
        (
            lambda a, b: options.GeoAttributePair(a, b, b),
            "geo-attr-pair",
            {
                "parent": [{"name": "a", "ns": ""}, {"name": "b", "ns": ""}],
                "lat": [{"name": "a", "ns": ""}, {"name": "b", "ns": ""}],
                "lon": [{"name": "a", "ns": ""}, {"name": "b", "ns": ""}],
            },
        ),
        (
            options.GeoJsonProperty,
            "geo-json-property",
            {"parent-property": ["a", "b"], "json-property": ["a", "b"]},
        ),
        (
            lambda a, b: options.GeoJsonPropertyPair(a, b, b),
            "geo-json-property-pair",
            {
                "parent-property": ["a", "b"],
                "lat-property": ["a", "b"],
                "lon-property": ["a", "b"],
            },
        ),
        (
            lambda a, _b: options.GeoPath(a),
            "geo-path",
            {"path-index": [{"text": "/a"}, {"text": "/b"}]},
        ),
        (
            lambda a, _b: options.GeoRegionPath(a),
            "geo-region-path",
            {"path-index": [{"text": "/a"}, {"text": "/b"}]},
        ),
    ],
)
def test_geospatial_definitions_snapshot_multiple_index_selectors(
    build,
    member,
    expected,
):
    if member in ("geo-path", "geo-region-path"):
        first = [PathIndex("/a"), PathIndex("/b")]
        second = []
    elif member.startswith("geo-json"):
        first = [JsonProperty("a"), JsonProperty("b")]
        second = first.copy()
    else:
        first = [Element("a"), Element("b")]
        second = (
            [Attribute("a"), Attribute("b")]
            if member == "geo-attr-pair"
            else first.copy()
        )
    definition = build(first, second)
    first.clear()
    second.clear()
    assert definition.to_json() == {member: expected}
    assert len(definition.to_xml()) == sum(len(value) for value in expected.values())


def test_nested_options_snapshot_collections_and_namespace_inputs():
    facet_options = ["limit=5"]
    term_options = ["exact"]
    sources = [options.MetadataQName(Element("title"))]
    paths = ["/d:doc/d:title"]
    bindings = {"d": "https://example.com/docs"}
    custom = options.CustomConstraint(
        "custom",
        options.Callback("parse"),
        facet_options=facet_options,
        term_options=term_options,
    )
    collection = options.Collection(options=facet_options)
    value = options.Value(Element("title"), options=term_options)
    extraction = options.ExtractDocumentData(paths, namespaces=bindings)
    metadata = options.ExtractMetadata(sources)
    facet_options.clear()
    term_options.clear()
    sources.clear()
    paths.clear()
    bindings.clear()
    assert custom.to_json() == {
        "constraint": {
            "name": "custom",
            "custom": {
                "parse": {"apply": "parse"},
                "facet-option": ["limit=5"],
                "term-option": ["exact"],
            },
        },
    }
    assert collection.to_json() == {"collection": {"facet-option": ["limit=5"]}}
    assert value.to_json() == {
        "value": {"element": {"name": "title", "ns": ""}, "term-option": ["exact"]},
    }
    assert extraction.to_json() == {
        "extract-document-data": {
            "extract-path": ["/d:doc/d:title"],
            "namespaces": {"d": "https://example.com/docs"},
        },
    }
    assert metadata.to_json() == {
        "extract-metadata": {"qname": [{"elem-name": "title", "elem-ns": ""}]},
    }
    value.to_json()["value"]["term-option"].clear()
    assert value.to_json()["value"]["term-option"] == ["exact"]


def test_minimal_defaults_for_suggestions_and_terms():
    assert options.SuggestionSource(ref="title").to_json() == {
        "suggestion-source": {"ref": "title"},
    }
    assert options.DefaultSuggestionSource().to_json() == {
        "default-suggestion-source": {},
    }
    assert options.Term().to_json() == {"term": {}}
    assert options.TermDefault(ref="title").to_json() == {"default": {"ref": "title"}}
    assert options.TermDefault().to_json() == {"default": {}}


def test_term_options_are_snapshotted_and_keep_empty_values():
    strings = ["case-insensitive", "unstemmed"]
    term = options.Term(options=strings, weight=0)
    strings.clear()
    assert term.to_json() == {
        "term": {"term-option": ["case-insensitive", "unstemmed"], "weight": 0},
    }
    assert tostring(term.to_xml(), encoding="unicode") == (
        '<search:term xmlns:search="http://marklogic.com/appservices/search">'
        "<search:weight>0</search:weight><search:term-option>case-insensitive"
        "</search:term-option><search:term-option>unstemmed</search:term-option></search:term>"
    )


def test_constraint_facet_options_override_shared_range_options_in_both_formats():
    index = Range(Element("price"), "xs:decimal", facet_options=["limit=5"])
    constraint = options.RangeConstraint("price", index, options=["limit=10"])
    assert constraint.to_json() == {
        "constraint": {
            "name": "price",
            "range": {
                "type": "xs:decimal",
                "element": {"name": "price", "ns": ""},
                "facet": True,
                "facet-option": ["limit=10"],
            },
        },
    }
    assert tostring(constraint.to_xml(), encoding="unicode") == (
        "<search:constraint "
        'xmlns:search="http://marklogic.com/appservices/search" name="price">'
        '<search:range type="xs:decimal" facet="true"><search:element '
        'name="price" ns="" />'
        "<search:facet-option>limit=10</search:facet-option></search:range></search:constraint>"
    )
    assert index.to_json()["range"]["facet-option"] == ["limit=5"]


def test_sort_reuses_only_the_index_selector_from_a_range_with_facet_settings():
    index = Range(
        Element("price"),
        "xs:decimal",
        nullable=True,
        facet=True,
        facet_options=["limit=5"],
        options=["cached"],
        fragment_scope="properties",
        weight=2,
        buckets=[options.Bucket("low", "Under ten", lt="10")],
    )
    sort = options.SortOrder(index, direction="descending")
    assert sort.to_json() == {
        "sort-order": {
            "type": "xs:decimal",
            "direction": "descending",
            "element": {"name": "price", "ns": ""},
        },
    }
    assert tostring(sort.to_xml(), encoding="unicode") == (
        '<search:sort-order xmlns:search="http://marklogic.com/appservices/search" '
        'type="xs:decimal" direction="descending"><search:element name="price" '
        'ns="" /></search:sort-order>'
    )
    assert index.nullable is True
    assert len(index.to_xml().findall(f"{{{SEARCH_NAMESPACE}}}bucket")) == 1


def test_word_collation_and_annotated_defaults_have_native_forms():
    word = options.Word(Element("title"), collation="http://marklogic.com/collation/")
    definition = options.TermDefault(word, annotation="Titles")
    assert definition.to_json() == {
        "default": {
            "word": {
                "element": {"name": "title", "ns": ""},
                "collation": "http://marklogic.com/collation/",
            },
            "annotation": ["Titles"],
        },
    }
    assert tostring(definition.to_xml(), encoding="unicode") == (
        '<search:default xmlns:search="http://marklogic.com/appservices/search">'
        "<search:word "
        'collation="http://marklogic.com/collation/">'
        '<search:element name="title" ns="" /></search:word>'
        "<search:annotation>Titles</search:annotation></search:default>"
    )
    constraint = options.WordConstraint(
        "title",
        Element("title"),
        collation="http://marklogic.com/collation/",
    )
    assert constraint.to_json() == {"constraint": {"name": "title", **word.to_json()}}


def test_custom_empty_term_callback_has_native_forms():
    term = options.Term(
        empty=options.Callback("empty", "https://example.com/search", "/search.xqy"),
    )
    assert term.to_json() == {
        "term": {
            "empty": {
                "apply": "empty",
                "ns": "https://example.com/search",
                "at": "/search.xqy",
            },
        },
    }
    assert tostring(term.to_xml(), encoding="unicode") == (
        '<search:term xmlns:search="http://marklogic.com/appservices/search">'
        '<search:empty apply="empty" ns="https://example.com/search" '
        'at="/search.xqy" /></search:term>'
    )


def test_sort_and_suggestion_annotations_have_native_forms():
    sort = SortOrder("score", annotation="Relevance")
    suggestion = options.SuggestionSource(ref="title", annotation="Titles")
    assert sort.to_json() == {
        "sort-order": {
            "direction": "ascending",
            "score": None,
            "annotation": ["Relevance"],
        },
    }
    assert suggestion.to_json() == {
        "suggestion-source": {"ref": "title", "annotation": ["Titles"]},
    }
    assert tostring(sort.to_xml(), encoding="unicode") == (
        "<search:sort-order "
        'xmlns:search="http://marklogic.com/appservices/search" direction="ascending">'
        "<search:score /><search:annotation>Relevance</search:annotation>"
        "</search:sort-order>"
    )
    assert tostring(suggestion.to_xml(), encoding="unicode") == (
        "<search:suggestion-source "
        'xmlns:search="http://marklogic.com/appservices/search" ref="title">'
        "<search:annotation>Titles</search:annotation></search:suggestion-source>"
    )


def test_named_suggestion_source_requires_a_constraint_reference():
    with pytest.raises(ValueError, match=r".") as error:
        options.SuggestionSource(options.WordLexicon())
    assert str(error.value) == "suggestion-source requires a constraint ref"
