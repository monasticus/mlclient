"""Public compilation and native serialization of TripleRangeQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import cts


def run():
    query = cts.triple_range_query("blue", "label", 2, operator=["!=", "=", ">"])
    assert query.to_json() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
