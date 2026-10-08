"""Collection query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import CollectionQuery, cts


def test_collection_query():
    query = cts.collection_query(["reports", "notes"])
    assert isinstance(query, CollectionQuery)
    assert query.serialize() == {"collectionQuery": {"uris": ["reports", "notes"]}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:collection-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:uri>reports</cts:uri><cts:uri>notes</cts:uri></cts:collection-query>"
    )
    assert query.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "cts:collection-query(($v0, $v1))",
        {"v0": "reports", "v1": "notes"},
    )


def test_collection_query_empty():
    assert cts.collection_query([]).serialize() == {"collectionQuery": {}}
