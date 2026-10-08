"""Native and not query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import AndNotQuery, cts


def test_and_not_query():
    query = cts.and_not_query(
        cts.collection_query("reports"),
        cts.collection_query("notes"),
    )
    assert isinstance(query, AndNotQuery)
    assert query.serialize() == {
        "andNotQuery": {
            "positiveQuery": {"collectionQuery": {"uris": ["reports"]}},
            "negativeQuery": {"collectionQuery": {"uris": ["notes"]}},
        },
    }
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:and-not-query xmlns:cts="http://marklogic.com/cts"><cts:positive><cts:collection-query><cts:uri>reports</cts:uri></cts:collection-query></cts:positive><cts:negative><cts:collection-query><cts:uri>notes</cts:uri></cts:collection-query></cts:negative></cts:and-not-query>'
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "declare variable $v1 as xs:string external;\n"
            "cts:and-not-query(cts:collection-query($v0), cts:collection-query($v1))"
        ),
        {"v0": "reports", "v1": "notes"},
    )
