"""Public compilation and native serialization of SimilarQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import FunctionCall, cts


def run():
    options = (
        '<options xmlns="cts:distinctive-terms"><min-val>1</min-'
        "val><min-weight>2</min-weight><complete>true</complete>"
        "</options>"
    )
    query = cts.similar_query(
        None,
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
    assert query.to_json() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
