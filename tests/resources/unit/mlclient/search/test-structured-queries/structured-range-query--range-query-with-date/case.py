"""Test RangeQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from datetime import date
from xml.etree import ElementTree
from mlclient.search.structured import Element, RangeQuery


def run():
    query = RangeQuery(Element("date"), date(2026, 1, 2))
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
