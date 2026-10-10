"""Public compilation and native serialization of ColumnRangeQuery."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import cts


def run():
    original = cts.column_range_query(
        "reports",
        "items",
        "price",
        2,
        operator=">=",
        options="cached",
        weight=2,
    )
    query = original.with_column_id(11548423394257569743)
    assert query.compile() == original.compile()
    assert original.column_id is None
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
