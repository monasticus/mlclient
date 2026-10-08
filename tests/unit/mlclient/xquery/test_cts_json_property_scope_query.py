"""Native json property scope query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import JsonPropertyScopeQuery, cts


def test_json_property_scope_query():
    query = cts.json_property_scope_query(["report", "note"], cts.true_query())
    assert isinstance(query, JsonPropertyScopeQuery)
    assert query.serialize() == {
        "jsonPropertyScopeQuery": {
            "property": ["report", "note"],
            "query": {"trueQuery": {}},
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:json-property-scope-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:property>report</cts:property>"
        "<cts:property>note</cts:property>"
        "<cts:true-query />"
        "</cts:json-property-scope-query>"
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "declare variable $v1 as xs:string external;\n"
            "cts:json-property-scope-query(($v0, $v1), cts:true-query())"
        ),
        {"v0": "report", "v1": "note"},
    )
