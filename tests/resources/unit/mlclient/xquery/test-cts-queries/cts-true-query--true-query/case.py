"""Native true query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import TrueQuery, cts


def run():
    query = cts.true_query()
    assert isinstance(query, TrueQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == ('xquery version "1.0-ml";\ncts:true-query()', {})
