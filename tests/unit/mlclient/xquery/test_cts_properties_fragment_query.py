"""Native properties fragment query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import PropertiesFragmentQuery, cts


def test_properties_fragment_query():
    query = cts.properties_fragment_query(cts.collection_query("reports"))
    assert isinstance(query, PropertiesFragmentQuery)
    assert query.serialize() == {
        "propertiesFragmentQuery": {
            "query": {"collectionQuery": {"uris": ["reports"]}},
        },
    }
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == '<cts:properties-fragment-query xmlns:cts="http://marklogic.com/cts"><cts:collection-query><cts:uri>reports</cts:uri></cts:collection-query></cts:properties-fragment-query>'
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "cts:properties-fragment-query(cts:collection-query($v0))"
        ),
        {"v0": "reports"},
    )
