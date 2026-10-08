"""Test container-constraint-query serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import ContainerConstraintQuery, TrueQuery


def test_serializes_to_json():
    query = ContainerConstraintQuery("section", TrueQuery())
    expected = {
        "container-constraint-query": {
            "constraint-name": "section",
            "true-query": None,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = ContainerConstraintQuery("section", TrueQuery())
    expected = ElementTree.fromstring(
        '<container-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>section</constraint-name>"
        "<true-query />"
        "</container-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
