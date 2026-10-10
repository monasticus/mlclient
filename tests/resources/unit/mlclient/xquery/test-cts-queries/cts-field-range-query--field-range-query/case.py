"""Native ``cts:field-range-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import FieldRangeQuery, cts


def run():
    query = cts.field_range_query("price", "<=", 2)
    assert isinstance(query, FieldRangeQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
