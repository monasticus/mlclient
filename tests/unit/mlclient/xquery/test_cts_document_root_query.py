"""Native ``cts:document-root-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import DocumentRootQuery, cts, fn

NS = "urn:mlclient:cts-test"


def test_document_root_query():
    query = cts.document_root_query("root")
    assert isinstance(query, DocumentRootQuery)
    assert query.serialize() == {"documentRootQuery": {"root": "root"}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:document-root-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:root>root</cts:root></cts:document-root-query>"
    )


def test_document_root_query_namespaced():
    query = cts.document_root_query(fn.qname(NS, "t:root"))
    assert isinstance(query, DocumentRootQuery)
    assert query.serialize() == {
        "documentRootQuery": {"root": "{urn:mlclient:cts-test}root"},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:document-root-query xmlns:cts="http://marklogic.com/cts">'
        '<cts:root xmlns:q="urn:mlclient:cts-test">q:root</cts:root>'
        "</cts:document-root-query>"
    )
