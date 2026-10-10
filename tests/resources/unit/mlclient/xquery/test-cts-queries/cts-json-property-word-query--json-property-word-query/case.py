"""Native json property word query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import JsonPropertyWordQuery, cts


def run():
    query = cts.json_property_word_query(
        ["title", "body"],
        ["blue", "green"],
        options=["lang=en", "exact"],
        weight=2,
    )
    assert isinstance(query, JsonPropertyWordQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ndeclare variable $v2 as xs:string external;\ndeclare "
            "variable $v3 as xs:string external;\ndeclare variable $v"
            "4 as xs:string external;\ndeclare variable $v5 as xs:str"
            "ing external;\ndeclare variable $v6 as xs:integer extern"
            "al;\ncts:json-property-word-query(($v0, $v1), ($v2, $v3)"
            ", ($v4, $v5), xs:double($v6))"
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
