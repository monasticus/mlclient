"""Test collection-constraint-query serialization."""

from xml.etree import ElementTree

from mlclient.search.structured import CollectionConstraintQuery


def test_serializes_to_json():
    query = CollectionConstraintQuery("category", ["blue", "green"])
    expected = {
        "collection-constraint-query": {
            "constraint-name": "category",
            "uri": ["blue", "green"],
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = CollectionConstraintQuery("category", ["blue", "green"])
    expected = ElementTree.fromstring(
        '<collection-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>category</constraint-name><uri>blue</uri><uri>green</uri>"
        "</collection-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
