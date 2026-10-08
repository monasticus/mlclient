"""Native ``cts:document-format-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import DocumentFormatQuery, cts


def test_document_format_query():
    query = cts.document_format_query("json")
    assert isinstance(query, DocumentFormatQuery)
    assert query.serialize() == {"documentFormatQuery": {"format": "json"}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:document-format-query xmlns:cts="http://marklogic.com/cts" format="'
        'json" />'
    )
