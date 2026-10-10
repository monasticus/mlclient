"""Native not query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import NotQuery, cts


def run():
    query = cts.not_query(cts.collection_query("reports"))
    assert isinstance(query, NotQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ncts:not-query(cts:collection-query($v0))"
        ),
        {"v0": "reports"},
    )
