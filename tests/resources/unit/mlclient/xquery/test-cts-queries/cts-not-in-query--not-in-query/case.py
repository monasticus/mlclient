"""Native not in query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import NotInQuery, cts


def run():
    query = cts.not_in_query(
        cts.collection_query("reports"),
        cts.collection_query("notes"),
    )
    assert isinstance(query, NotInQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ncts:not-in-query(cts:collection-query($v0), cts:coll"
            "ection-query($v1))"
        ),
        {"v0": "reports", "v1": "notes"},
    )
