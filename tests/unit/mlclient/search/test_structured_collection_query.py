"""Test CollectionQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import CollectionQuery


def test_collection_query_serializes_to_json():
    query = CollectionQuery(["reports", "notes"])
    expected = {"collection-query": {"uri": ["reports", "notes"]}}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_collection_query_serializes_to_xml():
    query = CollectionQuery(["reports", "notes"])
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<collection-query>"
        "<uri>reports</uri>"
        "<uri>notes</uri>"
        "</collection-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
