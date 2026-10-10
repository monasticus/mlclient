"""Public compilation and native serialization of ReverseQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ('{"label":"blue","count":2}',)),
    )
    assert query.to_json() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
