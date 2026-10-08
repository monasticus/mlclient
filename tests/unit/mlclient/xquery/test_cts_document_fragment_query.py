"""Native document fragment query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import DocumentFragmentQuery, cts


def test_document_fragment_query():
    query = cts.document_fragment_query(cts.collection_query("reports"))
    assert isinstance(query, DocumentFragmentQuery)
    assert query.serialize() == {
        "documentFragmentQuery": {"query": {"collectionQuery": {"uris": ["reports"]}}},
    }
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:document-fragment-query xmlns:cts="http://marklogic.com/cts"><cts:collection-query><cts:uri>reports</cts:uri></cts:collection-query></cts:document-fragment-query>'
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "cts:document-fragment-query(cts:collection-query($v0))"
        ),
        {"v0": "reports"},
    )
