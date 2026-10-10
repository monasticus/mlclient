"""Test LsqtQuery through its public API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import LsqtQuery


def run():
    query = LsqtQuery(
        "reports",
        timestamp="2024-01-01T00:00:00Z",
        options=["cached-incremental"],
        weight=2,
    )
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
