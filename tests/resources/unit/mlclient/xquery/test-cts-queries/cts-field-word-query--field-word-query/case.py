"""Native field word query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import FieldWordQuery, cts


def run():
    query = cts.field_word_query("title", "blue", options="lang=en", weight=2)
    assert isinstance(query, FieldWordQuery)
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
            "variable $v3 as xs:integer external;\ncts:field-word-que"
            "ry($v0, $v1, $v2, xs:double($v3))"
        ),
        {"v0": "title", "v1": "blue", "v2": "lang=en", "v3": "2"},
    )
