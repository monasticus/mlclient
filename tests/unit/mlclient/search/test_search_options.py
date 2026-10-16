"""Native serialization resources and public query behavior."""

from dataclasses import FrozenInstanceError
from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import tostring

import pytest

from mlclient.search.options import (
    PageLength,
    Range,
    ReturnFacets,
    SearchOptions,
    WordConstraint,
    opt,
)
from mlclient.search.structured import (
    Attribute,
    Element,
    Field,
    JsonProperty,
    PathIndex,
)

SEARCH_NAMESPACE = "http://marklogic.com/appservices/search"


def test_typed_constraint_survives_a_later_native_constraint():
    element = XmlElement(f"{{{SEARCH_NAMESPACE}}}constraint", {"name": "a"})
    options = opt.options(
        opt.word_constraint("b", Element("b")),
        opt.native({"constraint": {"name": "a"}}, element),
    )
    assert [c["name"] for c in options.to_json()["options"]["constraint"]] == ["b", "a"]


def test_search_options_are_not_equal_to_their_serialization():
    options = opt.options(opt.control("page-length", 5))
    assert options != options.to_json()


PRICE_RANGE = Range(Element("price"), "xs:decimal")


def test_search_options_with_the_same_definitions_are_equal():
    assert opt.options(
        opt.values("price", PRICE_RANGE),
        opt.control("page-length", 5),
    ) == opt.options(opt.values("price", PRICE_RANGE), opt.control("page-length", 5))
    assert opt.options(opt.values("price", PRICE_RANGE)) != opt.options(
        opt.sort(PRICE_RANGE),
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
        opt.options(opt.value_constraint("code", target, attribute=attribute))
    assert str(error.value) == (
        "value constraint attribute requires an Element target and an Attribute"
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_search_options_control_rejects_a_non_finite_float(value):
    with pytest.raises(ValueError, match="must be finite"):
        opt.options(opt.control("quality-weight", value))


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (
            lambda: opt.options(opt.word_constraint("label", "label")),
            ("word constraint target must be an Element, JsonProperty or Field"),
        ),
        (
            lambda: opt.options(opt.value_constraint("label", None)),
            ("value constraint target must be an Element, JsonProperty or Field"),
        ),
        (
            lambda: opt.options(opt.container_constraint("place", Field("place"))),
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
    options = opt.options(opt.native(definition, element))
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
            lambda values: opt.options(
                opt.values("price", PRICE_RANGE, options=values),
            ),
            "values",
            "values-option",
        ),
        (
            lambda values: opt.options(
                opt.range_constraint("price", PRICE_RANGE, options=values),
            ),
            "range",
            "facet-option",
        ),
        (
            lambda values: opt.options(
                opt.word_constraint("price", Element("price"), options=values),
            ),
            "word",
            "term-option",
        ),
        (
            lambda values: opt.options(
                opt.value_constraint("price", Element("price"), options=values),
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
        lambda index: opt.options(opt.values("price", index)),
        lambda index: opt.options(opt.tuples("pair", index, index)),
        lambda index: opt.options(opt.range_constraint("price", index)),
        lambda index: opt.options(opt.sort(index)),
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
        lambda index: opt.options(opt.values("price", index)),
        lambda index: opt.options(opt.tuples("pair", index, index)),
        lambda index: opt.options(opt.range_constraint("price", index)),
        lambda index: opt.options(opt.sort(index)),
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
    options = opt.options(
        opt.values("price", PRICE_RANGE),
        opt.control("page-length", 5),
    )
    assert repr(options) == "SearchOptions(values, page-length)"


def test_search_options_serialization_is_defensive():
    options = opt.options(opt.values("price", PRICE_RANGE))
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


def test_search_options_single_native_constraint_and_builder_constraints_accumulate():
    element = XmlElement(f"{{{SEARCH_NAMESPACE}}}constraint", {"name": "a"})
    options = opt.options(
        opt.native({"constraint": {"name": "a"}}, element),
        opt.word_constraint("b", Element("b")),
    )
    assert [c["name"] for c in options.to_json()["options"]["constraint"]] == ["a", "b"]
    assert [c.get("name") for c in options.to_xml()] == ["a", "b"]


@pytest.mark.parametrize(
    "build",
    [
        lambda target: opt.options(opt.word_constraint("label", target)),
        lambda target: opt.options(opt.value_constraint("label", target)),
        lambda target: opt.options(opt.container_constraint("label", target)),
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
    constraint = opt.word_constraint("title", Element("title"))
    defaults = opt.options(constraint, opt.page_length(10))
    paged = opt.options(defaults, opt.page_length(20), opt.return_facets(False))

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
    constraint = opt.word_constraint("title", Element("title"), options=terms)
    terms.append("case-sensitive")
    assert constraint.options == ("unstemmed",)
    with pytest.raises(FrozenInstanceError) as error:
        constraint.name = "changed"
    assert str(error.value) == "cannot assign to field 'name'"


@pytest.mark.parametrize("value", [True, 1.5, "20"])
def test_page_length_rejects_non_integer_values(value):
    with pytest.raises(TypeError) as error:
        opt.page_length(value)
    assert str(error.value) == "page length must be an integer"


@pytest.mark.parametrize("value", [0, -1])
def test_page_length_requires_a_positive_value(value):
    with pytest.raises(ValueError, match="page length must be positive") as error:
        opt.page_length(value)
    assert str(error.value) == "page length must be positive"


@pytest.mark.parametrize("value", [0, "false", None])
def test_return_facets_requires_a_boolean(value):
    with pytest.raises(TypeError) as error:
        opt.return_facets(value)
    assert str(error.value) == "return facets must be a boolean"


def test_options_rejects_non_option_components():
    with pytest.raises(TypeError) as error:
        opt.options({"page-length": 20})
    assert str(error.value) == (
        "options components must be SearchOption or SearchOptions instances"
    )


def test_option_classes_and_factories_build_equivalent_native_components():
    direct = SearchOptions(
        WordConstraint("title", Element("title")),
        PageLength(20),
        ReturnFacets(True),
    )
    built = opt.options(
        opt.word_constraint("title", Element("title")),
        opt.page_length(20),
        opt.return_facets(True),
    )
    assert direct == built
    assert built.to_json()["options"]["return-facets"] is True
    assert tostring(built.to_xml(), encoding="unicode").endswith(
        "<search:return-facets>true</search:return-facets></search:options>",
    )
