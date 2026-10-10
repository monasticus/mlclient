"""Native false query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import FalseQuery, cts


def run():
    query = cts.false_query()
    assert isinstance(query, FalseQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
    assert query.compile() == ('xquery version "1.0-ml";\ncts:false-query()', {})
