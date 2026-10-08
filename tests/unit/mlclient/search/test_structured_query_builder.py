"""Test structured-query composition through the public builder."""

from xml.etree import ElementTree

from mlclient.search.structured import StructuredQueryBuilder, sq


def test_builder_composes_range_and_term():
    query = sq.query(
        sq.and_(
            sq.range(sq.element("price"), 20, operator="GE", index_type="xs:int"),
            sq.term("blue"),
        ),
    )

    expected = ElementTree.fromstring(
        '<query xmlns="http://marklogic.com/appservices/search">'
        '<and-query><range-query type="xs:int">'
        '<element name="price" ns="" />'
        "<value>20</value><range-operator>GE</range-operator>"
        "</range-query><term-query><text>blue</text></term-query>"
        "</and-query></query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
    assert query.serialize() == {
        "query": {
            "queries": [
                {
                    "and-query": {
                        "queries": [
                            {
                                "range-query": {
                                    "type": "xs:int",
                                    "element": {"name": "price", "ns": ""},
                                    "value": "20",
                                    "range-operator": "GE",
                                },
                            },
                            {"term-query": {"text": ["blue"]}},
                        ],
                    },
                },
            ],
        },
    }


def test_builder_and_with_order():
    builder = StructuredQueryBuilder()
    query = builder.and_(builder.term("blue"), builder.term("green"), ordered=True)
    assert query.serialize() == {
        "and-query": {
            "queries": [
                {"term-query": {"text": ["blue"]}},
                {"term-query": {"text": ["green"]}},
                {"ordered": {"_value": True}},
            ],
        },
    }


def test_builder_or():
    query = sq.or_(sq.collection("reports"), sq.not_(sq.term("blue")))
    assert query.serialize() == {
        "or-query": {
            "queries": [
                {"collection-query": {"uri": ["reports"]}},
                {"not-query": {"term-query": {"text": ["blue"]}}},
            ],
        },
    }


def test_builder_near():
    query = sq.near(
        sq.term("blue"),
        sq.term("green"),
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    )
    assert query.serialize() == {
        "near-query": {
            "queries": [
                {"term-query": {"text": ["blue"]}},
                {"term-query": {"text": ["green"]}},
                {"distance": {"_value": 3.0}},
                {"minimum-distance": {"_value": 1.0}},
                {"distance-weight": {"_value": 2.0}},
                {"ordered": {"_value": False}},
            ],
        },
    }
