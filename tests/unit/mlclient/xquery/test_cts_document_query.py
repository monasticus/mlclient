"""Native document query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import DocumentQuery, cts


def test_document_query():
    query = cts.document_query(["/reports/a.xml", "/notes/b.json"])
    assert isinstance(query, DocumentQuery)
    assert query.serialize() == {
        "documentQuery": {"uris": ["/reports/a.xml", "/notes/b.json"]},
    }
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:document-query xmlns:cts="http://marklogic.com/cts"><cts:uri>/reports/a.xml</cts:uri><cts:uri>/notes/b.json</cts:uri></cts:document-query>'
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "declare variable $v1 as xs:string external;\n"
            "cts:document-query(($v0, $v1))"
        ),
        {"v0": "/reports/a.xml", "v1": "/notes/b.json"},
    )
