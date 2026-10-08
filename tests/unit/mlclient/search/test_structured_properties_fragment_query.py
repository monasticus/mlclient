"""Test PropertiesFragmentQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import PropertiesFragmentQuery, TermQuery


def test_properties_fragment_query_serializes_to_json():
    query = PropertiesFragmentQuery(TermQuery("blue"))
    expected = {"properties-fragment-query": {"term-query": {"text": ["blue"]}}}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_properties_fragment_query_serializes_to_xml():
    query = PropertiesFragmentQuery(TermQuery("blue"))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<properties-fragment-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "</properties-fragment-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
