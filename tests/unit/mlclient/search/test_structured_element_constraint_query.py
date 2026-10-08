"""Test element-constraint-query serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import ElementConstraintQuery, TrueQuery


def test_serializes_to_json():
    query = ElementConstraintQuery("section", TrueQuery())
    expected = {
        "element-constraint-query": {"constraint-name": "section", "true-query": None},
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = ElementConstraintQuery("section", TrueQuery())
    expected = ElementTree.fromstring(
        '<element-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>section</constraint-name><true-query />"
        "</element-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
