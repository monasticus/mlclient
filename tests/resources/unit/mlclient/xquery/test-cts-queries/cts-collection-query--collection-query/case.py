"""Collection query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import CollectionQuery, cts


def run():
    query = cts.collection_query(["reports", "notes"])
    assert isinstance(query, CollectionQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ncts:collection-query(($v0, $v1))"
        ),
        {"v0": "reports", "v1": "notes"},
    )
