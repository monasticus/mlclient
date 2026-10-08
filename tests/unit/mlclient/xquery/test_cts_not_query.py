"""Native not query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import NotQuery, cts


def test_not_query():
    query = cts.not_query(cts.collection_query("reports"))
    assert isinstance(query, NotQuery)
    assert query.serialize() == {
        "notQuery": {"query": {"collectionQuery": {"uris": ["reports"]}}},
    }
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:not-query xmlns:cts="http://marklogic.com/cts"><cts:collection-query><cts:uri>reports</cts:uri></cts:collection-query></cts:not-query>'
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "cts:not-query(cts:collection-query($v0))"
        ),
        {"v0": "reports"},
    )
