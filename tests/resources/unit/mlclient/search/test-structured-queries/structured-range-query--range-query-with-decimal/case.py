"""Test RangeQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from decimal import Decimal
from xml.etree import ElementTree
from mlclient.search.structured import JsonProperty, RangeQuery


def run():
    query = RangeQuery(JsonProperty("price"), Decimal("2.50"))
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
