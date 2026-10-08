"""Test properties-constraint-query serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import PropertiesConstraintQuery, TrueQuery


def test_serializes_to_json():
    query = PropertiesConstraintQuery("metadata", TrueQuery())
    expected = {
        "properties-constraint-query": {
            "constraint-name": "metadata",
            "true-query": None,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = PropertiesConstraintQuery("metadata", TrueQuery())
    expected = ElementTree.fromstring(
        '<properties-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>metadata</constraint-name><true-query />"
        "</properties-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
