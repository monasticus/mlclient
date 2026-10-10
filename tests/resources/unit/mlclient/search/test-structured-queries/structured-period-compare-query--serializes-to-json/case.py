"""Test PeriodCompareQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import PeriodCompareQuery


def run():
    query = PeriodCompareQuery("system", "aln_equals", "valid", options=["cached"])
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
