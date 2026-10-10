"""Native ``cts:field-value-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import FieldValueQuery, cts


def run():
    query = cts.field_value_query("price", ["1", "2"], weight=3)
    assert isinstance(query, FieldValueQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
