"""Native word-query serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import CtsQuery, WordQuery, cts


def run():
    query = cts.word_query("blue", options="lang=en")
    assert isinstance(query, WordQuery)
    assert isinstance(query, CtsQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(
        query.serialize("xml"),
        encoding="unicode",
    ) == read_query_expectation(__file__, "expected-2.xml")
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ncts:word-query($v0, $v1)"
        ),
        {"v0": "blue", "v1": "lang=en"},
    )
