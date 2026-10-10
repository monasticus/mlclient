"""Public compilation and native serialization of SimilarQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        weight=2,
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.to_json() == expected
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}
    assert tostring(
        query.serialize("xml"),
        encoding="unicode",
    ) == read_query_expectation(__file__, "expected-2.xml")
