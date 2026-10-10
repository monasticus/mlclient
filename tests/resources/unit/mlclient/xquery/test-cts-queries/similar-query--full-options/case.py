"""Public compilation and native serialization of SimilarQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import FunctionCall, cts


def run():
    options = (
        '<options xmlns="cts:distinctive-terms"><max-terms>20</m'
        "ax-terms><score>logtf</score></options>"
    )
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        weight=2,
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
    assert query.to_json() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
