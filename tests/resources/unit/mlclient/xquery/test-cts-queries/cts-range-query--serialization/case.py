"""Public compilation and native serialization of RangeQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import cts


def run():
    query = cts.range_query(
        cts.element_reference("price", options=["type=int", "unchecked"]),
        ">=",
        [2, 3],
        options="cached",
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
