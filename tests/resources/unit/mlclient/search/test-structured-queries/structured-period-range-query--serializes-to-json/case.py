"""Test PeriodRangeQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import Period, PeriodRangeQuery


def run():
    query = PeriodRangeQuery(
        ["valid", "system"],
        "aln_contains",
        [Period("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")],
        options=["cached"],
        weight=2,
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
