"""Native field word query serialization and compilation."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import FieldWordQuery, cts


def test_field_word_query():
    query = cts.field_word_query("title", "blue", options="lang=en", weight=2)
    assert isinstance(query, FieldWordQuery)
    assert query.serialize() == {
        "fieldWordQuery": {
            "field": ["title"],
            "text": ["blue"],
            "options": ["lang=en"],
            "weight": 2,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:field-word-query xmlns:cts="http://marklogic.com/cts" weight="2">'
        "<cts:field>title</cts:field>"
        "<cts:text>blue</cts:text>"
        "<cts:option>lang=en</cts:option>"
        "</cts:field-word-query>"
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\n'
            "declare variable $v0 as xs:string external;\n"
            "declare variable $v1 as xs:string external;\n"
            "declare variable $v2 as xs:string external;\n"
            "declare variable $v3 as xs:integer external;\n"
            "cts:field-word-query($v0, $v1, $v2, xs:double($v3))"
        ),
        {"v0": "title", "v1": "blue", "v2": "lang=en", "v3": "2"},
    )
