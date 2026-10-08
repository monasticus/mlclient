"""Native boost query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import BoostQuery, cts


def test_boost_query():
    query = cts.boost_query(
        cts.collection_query("reports"),
        cts.collection_query("notes"),
    )
    assert isinstance(query, BoostQuery)
    assert query.serialize() == {
        "boostQuery": {
            "matchingQuery": {"collectionQuery": {"uris": ["reports"]}},
            "boostingQuery": {"collectionQuery": {"uris": ["notes"]}},
        },
    }
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:boost-query xmlns:cts="http://marklogic.com/cts"><cts:matching-query><cts:collection-query><cts:uri>reports</cts:uri></cts:collection-query></cts:matching-query><cts:boosting-query><cts:collection-query><cts:uri>notes</cts:uri></cts:collection-query></cts:boosting-query></cts:boost-query>'
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "declare variable $v1 as xs:string external;\n"
            "cts:boost-query(cts:collection-query($v0), cts:collection-query($v1))"
        ),
        {"v0": "reports", "v1": "notes"},
    )
