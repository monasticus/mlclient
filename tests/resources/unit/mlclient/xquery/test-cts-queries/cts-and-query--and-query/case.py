"""Intersection serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import AndQuery, cts


def run():
    query = cts.and_query(
        [cts.word_query("blue", options="lang=en"), cts.collection_query("reports")],
        options="ordered",
    )
    assert isinstance(query, AndQuery)
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
            "variable $v3 as xs:string external;\ncts:and-query((cts:"
            "word-query($v0, $v1), cts:collection-query($v2)), $v3)"
        ),
        {"v0": "blue", "v1": "lang=en", "v2": "reports", "v3": "ordered"},
    )
