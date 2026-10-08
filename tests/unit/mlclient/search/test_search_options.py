"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement, tostring

import pytest

from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import (
    Attribute, Element, Field, JsonProperty, PathIndex,
)

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def test_empty_options():
    options = SearchOptions()

    assert options.serialize() == {"options": {}}
    assert tostring(options.serialize("xml"), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}" />'
    )


def test_values_range():
    options = SearchOptions().values("price", PRICE, options=["frequency-order"])

    assert options.to_json() == {
        "options": {
            "values": [
                {
                    "name": "price",
                    "range": {
                        "type": "xs:decimal",
                        "element": {"name": "price", "ns": ""},
                    },
                    "values-option": ["frequency-order"],
                },
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:values name="price">'
        '<search:range type="xs:decimal"><search:element name="price" ns="" />'
        "</search:range><search:values-option>frequency-order</search:values-option>"
        "</search:values></search:options>"
    )


def test_uri_lexicon():
    options = SearchOptions().values("uris", "uri")

    assert options.to_json() == {"options": {"values": [{"name": "uris", "uri": None}]}}
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:values name="uris">'
        "<search:uri /></search:values></search:options>"
    )


def test_collection_lexicon():
    options = SearchOptions().values("collections", "collection")

    assert options.to_json() == {
        "options": {"values": [{"name": "collections", "collection": None}]},
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:values name="collections">'
        "<search:collection /></search:values></search:options>"
    )


def test_tuple_definition():
    options = SearchOptions().tuples("prices", PRICE, Range(Element("day"), "xs:date"))

    assert options.to_json() == {
        "options": {
            "tuples": [
                {
                    "name": "prices",
                    "range": [
                        {"type": "xs:decimal", "element": {"name": "price", "ns": ""}},
                        {"type": "xs:date", "element": {"name": "day", "ns": ""}},
                    ],
                },
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:tuples name="prices">'
        '<search:range type="xs:decimal">'
        '<search:element name="price" ns="" /></search:range>'
        '<search:range type="xs:date">'
        '<search:element name="day" ns="" /></search:range>'
        "</search:tuples></search:options>"
    )


def test_range_constraint():
    options = SearchOptions().range_constraint("price", PRICE, options=["limit=10"])

    assert options.to_json() == {
        "options": {
            "constraint": [
                {
                    "name": "price",
                    "range": {
                        "type": "xs:decimal",
                        "element": {"name": "price", "ns": ""},
                        "facet": True,
                        "facet-option": ["limit=10"],
                    },
                },
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:constraint name="price">'
        '<search:range type="xs:decimal" facet="true">'
        '<search:element name="price" ns="" />'
        "<search:facet-option>limit=10</search:facet-option></search:range>"
        "</search:constraint></search:options>"
    )


def test_non_faceted_constraint():
    options = SearchOptions().range_constraint("price", PRICE, facet=False)

    assert options.to_json() == {
        "options": {
            "constraint": [
                {
                    "name": "price",
                    "range": {
                        "type": "xs:decimal",
                        "element": {"name": "price", "ns": ""},
                        "facet": False,
                    },
                },
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:constraint name="price">'
        '<search:range type="xs:decimal" facet="false">'
        '<search:element name="price" ns="" />'
        "</search:range></search:constraint></search:options>"
    )


def test_sort_definition():
    options = SearchOptions().sort(PRICE, direction="descending")

    assert options.to_json() == {
        "options": {
            "sort-order": [
                {
                    "type": "xs:decimal",
                    "element": {"name": "price", "ns": ""},
                    "direction": "descending",
                },
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:sort-order type="xs:decimal" '
        'direction="descending"><search:element name="price" ns="" />'
        "</search:sort-order></search:options>"
    )


def test_scalar_controls():
    options = SearchOptions().control("return-facets", False).control("page-length", 20)

    assert options.to_json() == {"options": {"return-facets": False, "page-length": 20}}
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}">'
        "<search:return-facets>false</search:return-facets>"
        "<search:page-length>20</search:page-length></search:options>"
    )


def test_replacing_scalar_control():
    options = SearchOptions().control("page-length", 10).control("page-length", 20)

    assert options.to_json() == {"options": {"page-length": 20}}
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}">'
        "<search:page-length>20</search:page-length>"
        "</search:options>"
    )


def test_native_options_are_copied():
    definition = {"transform-results": {"apply": "empty-snippet"}}
    element = XmlElement(f"{{{NS}}}transform-results", {"apply": "empty-snippet"})
    options = SearchOptions().add(definition, element)
    definition["transform-results"]["apply"] = "raw"
    element.set("apply", "raw")

    assert options.to_json() == {
        "options": {"transform-results": {"apply": "empty-snippet"}},
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}">'
        '<search:transform-results apply="empty-snippet" />'
        "</search:options>"
    )


def test_serialization_is_defensive():
    options = SearchOptions().values("price", PRICE)
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
        f'<search:options xmlns:search="{NS}"><search:values name="price">'
        '<search:range type="xs:decimal">'
        '<search:element name="price" ns="" /></search:range>'
        "</search:values></search:options>"
    )


def test_invalid_values_index():
    with pytest.raises(TypeError) as error:
        SearchOptions().values("price", "unsupported")
    assert str(error.value) == "values index must be a Range, uri or collection"


def test_insufficient_tuple_indexes():
    with pytest.raises(ValueError, match="requires at least") as error:
        SearchOptions().tuples("price", PRICE)
    assert str(error.value) == "tuples requires at least two range indexes"


def test_invalid_tuple_index():
    with pytest.raises(TypeError) as error:
        SearchOptions().tuples("price", PRICE, "day")
    assert str(error.value) == "tuples indexes must be Range instances"


def test_invalid_constraint_index():
    with pytest.raises(TypeError) as error:
        SearchOptions().range_constraint("price", "price")
    assert str(error.value) == "range constraint index must be a Range"


def test_invalid_sort_index():
    with pytest.raises(TypeError) as error:
        SearchOptions().sort("price")
    assert str(error.value) == "sort index must be a Range"


def test_invalid_sort_direction():
    with pytest.raises(ValueError, match="sort direction") as error:
        SearchOptions().sort(PRICE, direction="up")
    assert str(error.value) == "sort direction must be ascending or descending"


def test_invalid_control_value():
    with pytest.raises(TypeError) as error:
        SearchOptions().control("return-facets", [])
    assert str(error.value) == "control value must be a string, number or boolean"


def test_native_list_members_append_in_both_formats():
    first = XmlElement(f"{{{NS}}}operator", {"name": "sort"})
    second = XmlElement(f"{{{NS}}}operator", {"name": "page"})
    options = SearchOptions().add(
        {"operator": [{"name": "sort"}, {"name": "page"}]},
        first,
        second,
    )

    assert options.to_json() == {
        "options": {"operator": [{"name": "sort"}, {"name": "page"}]},
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}">'
        '<search:operator name="sort" /><search:operator name="page" />'
        "</search:options>"
    )


def test_native_scalar_member_replaces_a_control_in_both_formats():
    replacement = XmlElement(f"{{{NS}}}page-length")
    replacement.text = "50"
    options = (
        SearchOptions()
        .control("page-length", 10)
        .control("return-facets", False)
        .add({"page-length": 50}, replacement)
    )

    assert options.to_json() == {"options": {"return-facets": False, "page-length": 50}}
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}">'
        "<search:return-facets>false</search:return-facets>"
        "<search:page-length>50</search:page-length></search:options>"
    )


def test_native_member_without_xml_is_rejected():
    with pytest.raises(ValueError, match="add requires") as error:
        SearchOptions().add({"return-facets": False})

    assert str(error.value) == (
        "add requires one search-namespace XML element per JSON definition; "
        "return-facets has 1 JSON and 0 XML definitions"
    )


def test_native_xml_without_json_is_rejected():
    element = XmlElement(f"{{{NS}}}return-facets")

    with pytest.raises(ValueError, match="add requires") as error:
        SearchOptions().add({}, element)

    assert str(error.value) == (
        "add requires one search-namespace XML element per JSON definition; "
        "return-facets has 0 JSON and 1 XML definitions"
    )


def test_native_xml_outside_search_namespace_is_rejected():
    with pytest.raises(ValueError, match="add requires") as error:
        SearchOptions().add({"page-length": 5}, XmlElement("page-length"))

    assert str(error.value) == (
        f"add requires XML elements in the {NS} namespace; got page-length"
    )


def test_builders_with_the_same_definitions_are_equal():
    assert SearchOptions().values("price", PRICE).control("page-length", 5) == (
        SearchOptions().values("price", PRICE).control("page-length", 5)
    )
    assert SearchOptions().values("price", PRICE) != SearchOptions().sort(PRICE)


def test_builder_is_not_equal_to_its_serialization():
    options = SearchOptions().control("page-length", 5)

    assert options != options.to_json()


def test_repr_names_the_definitions():
    options = SearchOptions().values("price", PRICE).control("page-length", 5)

    assert repr(options) == "SearchOptions(values, page-length)"


def test_word_constraint_on_an_element():
    options = SearchOptions().word_constraint(
        "label",
        Element("label", "urn:x"),
        options=["case-insensitive", "unstemmed"],
    )

    assert options.to_json() == {
        "options": {
            "constraint": [
                {
                    "name": "label",
                    "word": {
                        "element": {"name": "label", "ns": "urn:x"},
                        "term-option": ["case-insensitive", "unstemmed"],
                    },
                },
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:constraint name="label">'
        '<search:word><search:element name="label" ns="urn:x" />'
        "<search:term-option>case-insensitive</search:term-option>"
        "<search:term-option>unstemmed</search:term-option>"
        "</search:word></search:constraint></search:options>"
    )


def test_value_constraint_on_a_json_property_with_one_option():
    options = SearchOptions().value_constraint(
        "label",
        JsonProperty("label"),
        options="case-sensitive",
    )

    assert options.to_json() == {
        "options": {
            "constraint": [
                {
                    "name": "label",
                    "value": {
                        "json-property": "label",
                        "term-option": ["case-sensitive"],
                    },
                },
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:constraint name="label">'
        "<search:value><search:json-property>label</search:json-property>"
        "<search:term-option>case-sensitive</search:term-option>"
        "</search:value></search:constraint></search:options>"
    )


def test_word_constraint_on_an_attribute():
    options = SearchOptions().word_constraint(
        "code",
        Element("item"),
        attribute=Attribute("code"),
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
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:constraint name="code">'
        '<search:word><search:element name="item" ns="" />'
        '<search:attribute name="code" ns="" /></search:word>'
        "</search:constraint></search:options>"
    )


def test_value_constraint_with_a_json_node_type():
    options = SearchOptions().value_constraint(
        "price",
        JsonProperty("price"),
        node_type="number",
    )

    assert options.to_json()["options"]["constraint"] == [
        {"name": "price", "value": {"type": "number", "json-property": "price"}},
    ]
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:constraint name="price">'
        '<search:value type="number"><search:json-property>price'
        "</search:json-property></search:value></search:constraint>"
        "</search:options>"
    )


def test_value_constraint_rejects_an_unknown_json_node_type():
    with pytest.raises(ValueError, match="node_type must be one of") as error:
        SearchOptions().value_constraint(
            "price",
            JsonProperty("price"),
            node_type="int",
        )

    assert str(error.value) == (
        "value constraint node_type must be one of boolean, null, number, string, "
        "got 'int'"
    )


@pytest.mark.parametrize(
    ("target", "attribute"),
    [(JsonProperty("item"), Attribute("code")), (Element("item"), Element("code"))],
)
def test_constraint_attribute_requires_an_element_and_an_attribute(target, attribute):
    with pytest.raises(TypeError) as error:
        SearchOptions().value_constraint("code", target, attribute=attribute)

    assert str(error.value) == (
        "value constraint attribute requires an Element target and an Attribute"
    )


def test_collection_constraint_calculates_a_facet_by_default():
    options = SearchOptions().collection_constraint("type")

    assert options.to_json()["options"]["constraint"] == [
        {"name": "type", "collection": {"facet": True}},
    ]


def test_word_constraint_on_a_field():
    options = SearchOptions().word_constraint("summary", Field("summary"))

    assert options.to_json() == {
        "options": {
            "constraint": [{"name": "summary", "word": {"field": {"name": "summary"}}}],
        },
    }


def test_collection_constraint():
    options = SearchOptions().collection_constraint("type", prefix="cts-", facet=True)

    assert options.to_json() == {
        "options": {
            "constraint": [
                {"name": "type", "collection": {"facet": True, "prefix": "cts-"}},
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:constraint name="type">'
        '<search:collection facet="true" prefix="cts-" />'
        "</search:constraint></search:options>"
    )


def test_container_constraint():
    options = SearchOptions().container_constraint("place", Element("location"))

    assert options.to_json() == {
        "options": {
            "constraint": [
                {
                    "name": "place",
                    "container": {"element": {"name": "location", "ns": ""}},
                },
            ],
        },
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}"><search:constraint name="place">'
        '<search:container><search:element name="location" ns="" />'
        "</search:container></search:constraint></search:options>"
    )


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (
            lambda: SearchOptions().word_constraint("label", "label"),
            "word constraint target must be an Element, JsonProperty or Field",
        ),
        (
            lambda: SearchOptions().value_constraint("label", None),
            "value constraint target must be an Element, JsonProperty or Field",
        ),
        (
            lambda: SearchOptions().container_constraint("place", Field("place")),
            "container constraint target must be an Element or JsonProperty",
        ),
    ],
)
def test_invalid_constraint_targets(build, message):
    with pytest.raises(TypeError) as error:
        build()
    assert str(error.value) == message


def test_one_option_string_is_one_option():
    options = SearchOptions().values("price", PRICE, options="frequency-order")

    assert options.to_json()["options"]["values"][0]["values-option"] == [
        "frequency-order",
    ]


def test_single_native_constraint_and_builder_constraints_accumulate():
    element = XmlElement(f"{{{NS}}}constraint", {"name": "a"})
    options = (
        SearchOptions()
        .add({"constraint": {"name": "a"}}, element)
        .word_constraint("b", Element("b"))
    )

    assert [c["name"] for c in options.to_json()["options"]["constraint"]] == [
        "a",
        "b",
    ]
    assert [c.get("name") for c in options.to_xml()] == ["a", "b"]


def test_builder_constraint_survives_a_later_native_constraint():
    element = XmlElement(f"{{{NS}}}constraint", {"name": "a"})
    options = (
        SearchOptions()
        .word_constraint("b", Element("b"))
        .add({"constraint": {"name": "a"}}, element)
    )

    assert [c["name"] for c in options.to_json()["options"]["constraint"]] == [
        "b",
        "a",
    ]


def test_repeatable_controls_accumulate():
    options = (
        SearchOptions()
        .control("search-option", "unfiltered")
        .control("search-option", "score-simple")
    )

    assert options.to_json() == {
        "options": {"search-option": ["unfiltered", "score-simple"]},
    }
    assert tostring(options.to_xml(), encoding="unicode") == (
        f'<search:options xmlns:search="{NS}">'
        "<search:search-option>unfiltered</search:search-option>"
        "<search:search-option>score-simple</search:search-option>"
        "</search:options>"
    )


def test_control_accepts_a_finite_float():
    options = SearchOptions().control("quality-weight", 0.5)

    assert options.to_json() == {"options": {"quality-weight": 0.5}}


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_control_rejects_a_non_finite_float(value):
    with pytest.raises(ValueError, match="must be finite"):
        SearchOptions().control("quality-weight", value)


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
def test_range_components_serialize_only_when_requested(build):
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


@pytest.mark.parametrize(
    "build",
    [
        lambda target: SearchOptions().word_constraint("label", target),
        lambda target: SearchOptions().value_constraint("label", target),
        lambda target: SearchOptions().container_constraint("label", target),
    ],
    ids=["word-constraint", "value-constraint", "container-constraint"],
)
def test_target_components_serialize_only_when_requested(build):
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


@pytest.mark.parametrize(
    ("build", "member", "option_name"),
    [
        (
            lambda values: SearchOptions().values("price", PRICE, options=values),
            "values",
            "values-option",
        ),
        (
            lambda values: SearchOptions().range_constraint(
                "price", PRICE, options=values,
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
def test_option_lists_are_snapshotted_before_serialization(build, member, option_name):
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
def test_path_namespaces_remain_snapshotted_and_serializable(build):
    namespaces = {"p": "urn:prices"}
    index = Range(PathIndex("/p:price", namespaces), "xs:decimal")
    options = build(index)
    namespaces["p"] = "urn:changed"
    assert "urn:prices" in str(options.to_json())
    assert "urn:changed" not in str(options.to_json())
    xml = tostring(options.to_xml(), encoding="unicode")
    assert "urn:prices" in xml
    assert "urn:changed" not in xml
