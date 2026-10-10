"""Native ``cts:element-range-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
import datetime
from decimal import Decimal
from xml.etree.ElementTree import tostring
from mlclient.xquery import ElementRangeQuery, cts

START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def run():
    query = cts.element_range_query("price", "<", Decimal("1.5"))
    assert isinstance(query, ElementRangeQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
