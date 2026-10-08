"""Native locks fragment query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import LocksFragmentQuery, cts


def test_locks_fragment_query():
    query = cts.locks_fragment_query(cts.collection_query("reports"))
    assert isinstance(query, LocksFragmentQuery)
    assert query.serialize() == {
        "locksFragmentQuery": {"query": {"collectionQuery": {"uris": ["reports"]}}},
    }
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:locks-fragment-query xmlns:cts="http://marklogic.com/cts"><cts:collection-query><cts:uri>reports</cts:uri></cts:collection-query></cts:locks-fragment-query>'
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "cts:locks-fragment-query(cts:collection-query($v0))"
        ),
        {"v0": "reports"},
    )
