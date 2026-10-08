"""Test DocumentFragmentQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import DocumentFragmentQuery, TermQuery


def test_document_fragment_query_serializes_to_json():
    query = DocumentFragmentQuery(TermQuery("blue"))
    expected = {"document-fragment-query": {"term-query": {"text": ["blue"]}}}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_document_fragment_query_serializes_to_xml():
    query = DocumentFragmentQuery(TermQuery("blue"))
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<document-fragment-query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "</document-fragment-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
