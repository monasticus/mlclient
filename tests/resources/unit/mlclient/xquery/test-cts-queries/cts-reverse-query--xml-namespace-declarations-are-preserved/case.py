"""Public compilation and native serialization of ReverseQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import FunctionCall, cts


def run():
    source = '<report xmlns:r="urn:reports" kind="r:blue">blue</report>'
    query = cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
    assert query.to_json() == {"reverseQuery": {"nodes": [source]}}
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-1.xml",
    )
