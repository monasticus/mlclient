"""Test PeriodRangeQuery through its public API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import Period, PeriodRangeQuery


def run():
    query = PeriodRangeQuery(
        ["valid", "system"],
        "aln_contains",
        [Period("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")],
        options=["cached"],
        weight=2,
    )
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
