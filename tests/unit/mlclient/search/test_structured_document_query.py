"""Test DocumentQuery through the public structured-query API."""

from xml.etree import ElementTree

from mlclient.search.structured import DocumentQuery


def test_document_query_serializes_to_json():
    query = DocumentQuery(["/reports/first.xml", "/reports/second.json"])
    expected = {
        "document-query": {"uri": ["/reports/first.xml", "/reports/second.json"]},
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_document_query_serializes_to_xml():
    query = DocumentQuery(["/reports/first.xml", "/reports/second.json"])
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<document-query>"
        "<uri>/reports/first.xml</uri>"
        "<uri>/reports/second.json</uri>"
        "</document-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
