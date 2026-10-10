"""Test RangeQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from datetime import datetime
from xml.etree import ElementTree
from mlclient.search.structured import Field, RangeQuery


def run():
    query = RangeQuery(Field("price"), datetime(2026, 1, 2, 3, 4, 5))
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
