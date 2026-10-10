"""Native locks fragment query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import LocksFragmentQuery, cts


def run():
    query = cts.locks_fragment_query(cts.collection_query("reports"))
    assert isinstance(query, LocksFragmentQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ncts:locks-fragment-query(cts:collection-q"
            "uery($v0))"
        ),
        {"v0": "reports"},
    )
