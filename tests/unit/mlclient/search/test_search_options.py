"""Native serialization resources and public query behavior."""

import pytest
from xml.etree.ElementTree import tostring
from tests.utils.resources import discover_serialization_cases
from xml.etree.ElementTree import Element as XmlElement
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element
from mlclient.search.structured import Attribute, JsonProperty
from mlclient.search.structured import Field
from mlclient.search.structured import PathIndex


@pytest.mark.parametrize(
    "case", discover_serialization_cases(__file__), ids=lambda case: case.name,
)
def test_serialization(case):
    case.assert_matches()


SEARCH_NAMESPACE = "http://marklogic.com/appservices/search"


def test_search_options_builder_constraint_survives_a_later_native_constraint():
    element = XmlElement(f"{{{SEARCH_NAMESPACE}}}constraint", {"name": "a"})
    options = (
        SearchOptions()
        .word_constraint("b", Element("b"))
        .add({"constraint": {"name": "a"}}, element)
    )
    assert [c["name"] for c in options.to_json()["options"]["constraint"]] == ["b", "a"]


def test_search_options_builder_is_not_equal_to_its_serialization():
    options = SearchOptions().control("page-length", 5)
    assert options != options.to_json()


PRICE_RANGE = Range(Element("price"), "xs:decimal")


def test_search_options_builders_with_the_same_definitions_are_equal():
    assert SearchOptions().values("price", PRICE_RANGE).control(
        "page-length", 5,
    ) == SearchOptions().values("price", PRICE_RANGE).control("page-length", 5)
    assert SearchOptions().values("price", PRICE_RANGE) != SearchOptions().sort(
        PRICE_RANGE,
    )


def test_search_options_collection_constraint_calculates_a_facet_by_default():
    options = SearchOptions().collection_constraint("type")
    assert options.to_json()["options"]["constraint"] == [
        {"name": "type", "collection": {"facet": True}},
    ]


@pytest.mark.parametrize(
    ("target", "attribute"),
    [(JsonProperty("item"), Attribute("code")), (Element("item"), Element("code"))],
)
def test_search_options_constraint_attribute_requires_an_element_and_an_attribute(
    target, attribute,
):
    with pytest.raises(TypeError) as error:
        SearchOptions().value_constraint("code", target, attribute=attribute)
    assert (
        str(error.value)
        == (
            "value constraint attribute requires an Element target a"
            "nd an Attribute"
        )
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_search_options_control_rejects_a_non_finite_float(value):
    with pytest.raises(ValueError, match="must be finite"):
        SearchOptions().control("quality-weight", value)


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (
            lambda: SearchOptions().word_constraint("label", "label"),
            (
                "word constraint target must be an Element, JsonProperty"
                " or Field"
            ),
        ),
        (
            lambda: SearchOptions().value_constraint("label", None),
            (
                "value constraint target must be an Element, JsonPropert"
                "y or Field"
            ),
        ),
        (
            lambda: SearchOptions().container_constraint("place", Field("place")),
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
        f"{{{SEARCH_NAMESPACE}}}transform-results", {"apply": "empty-snippet"},
    )
    options = SearchOptions().add(definition, element)
    definition["transform-results"]["apply"] = "raw"
    element.set("apply", "raw")
    assert options.to_json() == {
        "options": {"transform-results": {"apply": "empty-snippet"}},
    }
    assert (
        tostring(options.to_xml(), encoding="unicode")
        == (
            '<search:options xmlns:search="http://marklogic.com/apps'
            'ervices/search"><search:transform-results apply="empty-'
            'snippet" /></search:options>'
        )
    )


def test_search_options_one_option_string_is_one_option():
    options = SearchOptions().values("price", PRICE_RANGE, options="frequency-order")
    assert options.to_json()["options"]["values"][0]["values-option"] == [
        "frequency-order",
    ]


@pytest.mark.parametrize(
    ("build", "member", "option_name"),
    [
        (
            lambda values: SearchOptions().values("price", PRICE_RANGE, options=values),
            "values",
            "values-option",
        ),
        (
            lambda values: SearchOptions().range_constraint(
                "price", PRICE_RANGE, options=values,
            ),
            "range",
            "facet-option",
        ),
        (
            lambda values: SearchOptions().word_constraint(
                "price", Element("price"), options=values,
            ),
            "word",
            "term-option",
        ),
        (
            lambda values: SearchOptions().value_constraint(
                "price", Element("price"), options=values,
            ),
            "value",
            "term-option",
        ),
    ],
)
def test_search_options_option_lists_are_snapshotted_before_serialization(
    build, member, option_name,
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
        lambda index: SearchOptions().values("price", index),
        lambda index: SearchOptions().tuples("pair", index, index),
        lambda index: SearchOptions().range_constraint("price", index),
        lambda index: SearchOptions().sort(index),
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
        lambda index: SearchOptions().values("price", index),
        lambda index: SearchOptions().tuples("pair", index, index),
        lambda index: SearchOptions().range_constraint("price", index),
        lambda index: SearchOptions().sort(index),
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
    options = SearchOptions().values("price", PRICE_RANGE).control("page-length", 5)
    assert repr(options) == "SearchOptions(values, page-length)"


def test_search_options_serialization_is_defensive():
    options = SearchOptions().values("price", PRICE_RANGE)
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
    assert (
        tostring(options.to_xml(), encoding="unicode")
        == (
            '<search:options xmlns:search="http://marklogic.com/apps'
            'ervices/search"><search:values name="price"><search:ran'
            'ge type="xs:decimal"><search:element name="price" ns=""'
            ' /></search:range></search:values></search:options>'
        )
    )


def test_search_options_single_native_constraint_and_builder_constraints_accumulate():
    element = XmlElement(f"{{{SEARCH_NAMESPACE}}}constraint", {"name": "a"})
    options = (
        SearchOptions()
        .add({"constraint": {"name": "a"}}, element)
        .word_constraint("b", Element("b"))
    )
    assert [c["name"] for c in options.to_json()["options"]["constraint"]] == ["a", "b"]
    assert [c.get("name") for c in options.to_xml()] == ["a", "b"]


@pytest.mark.parametrize(
    "build",
    [
        lambda target: SearchOptions().word_constraint("label", target),
        lambda target: SearchOptions().value_constraint("label", target),
        lambda target: SearchOptions().container_constraint("label", target),
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


def test_search_options_value_constraint_with_a_json_node_type():
    options = SearchOptions().value_constraint(
        "price", JsonProperty("price"), node_type="number",
    )
    assert options.to_json()["options"]["constraint"] == [
        {"name": "price", "value": {"type": "number", "json-property": "price"}},
    ]


def test_search_options_word_constraint_on_an_attribute():
    options = SearchOptions().word_constraint(
        "code", Element("item"), attribute=Attribute("code"),
    )
    assert options.to_json()["options"]["constraint"] == [
        {
            "name": "code",
            "word": {
                "element": {"name": "item", "ns": ""},
                "attribute": {"name": "code", "ns": ""},
            },
        },
    ]
