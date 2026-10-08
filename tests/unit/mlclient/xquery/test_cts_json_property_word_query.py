"""Native json property word query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import JsonPropertyWordQuery, cts


def test_json_property_word_query():
    query = cts.json_property_word_query(
        ["title", "body"],
        ["blue", "green"],
        options=["lang=en", "exact"],
        weight=2,
    )
    assert isinstance(query, JsonPropertyWordQuery)
    assert query.serialize() == {
        "jsonPropertyWordQuery": {
            "property": ["title", "body"],
            "text": ["blue", "green"],
            "options": ["lang=en", "exact"],
            "weight": 2,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:json-property-word-query xmlns:cts="http://marklogic.com/cts" wei'
        'ght="2">'
        "<cts:property>title</cts:property>"
        "<cts:property>body</cts:property>"
        "<cts:text>blue</cts:text>"
        "<cts:text>green</cts:text>"
        "<cts:option>lang=en</cts:option>"
        "<cts:option>exact</cts:option>"
        "</cts:json-property-word-query>"
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "declare variable $v1 as xs:string external;\n"
            "declare variable $v2 as xs:string external;\n"
            "declare variable $v3 as xs:string external;\n"
            "declare variable $v4 as xs:string external;\n"
            "declare variable $v5 as xs:string external;\n"
            "declare variable $v6 as xs:integer external;\n"
            "cts:json-property-word-query(($v0, $v1), ($v2, $v3), ($v4, $v5), xs:do"
            "uble($v6))"
        ),
        {
            "v0": "title",
            "v1": "body",
            "v2": "blue",
            "v3": "green",
            "v4": "lang=en",
            "v5": "exact",
            "v6": "2",
        },
    )
