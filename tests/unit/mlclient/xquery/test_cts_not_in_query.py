"""Native not in query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import NotInQuery, cts


def test_not_in_query():
    query = cts.not_in_query(
        cts.collection_query("reports"),
        cts.collection_query("notes"),
    )
    assert isinstance(query, NotInQuery)
    assert query.serialize() == {
        "notInQuery": {
            "positiveQuery": {"collectionQuery": {"uris": ["reports"]}},
            "negativeQuery": {"collectionQuery": {"uris": ["notes"]}},
        },
    }
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:not-in-query xmlns:cts="http://marklogic.com/cts"><cts:positive><cts:collection-query><cts:uri>reports</cts:uri></cts:collection-query></cts:positive><cts:negative><cts:collection-query><cts:uri>notes</cts:uri></cts:collection-query></cts:negative></cts:not-in-query>'
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "declare variable $v1 as xs:string external;\n"
            "cts:not-in-query(cts:collection-query($v0), cts:collection-query($v1))"
        ),
        {"v0": "reports", "v1": "notes"},
    )
