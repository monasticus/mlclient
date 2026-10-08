"""Test LocksFragmentQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import LocksFragmentQuery, TermQuery


def test_locks_fragment_query_serializes_to_json():
    query = LocksFragmentQuery(TermQuery("blue"))
    expected = {"locks-fragment-query": {"term-query": {"text": ["blue"]}}}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_locks_fragment_query_serializes_to_xml():
    query = LocksFragmentQuery(TermQuery("blue"))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<locks-fragment-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "</locks-fragment-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
