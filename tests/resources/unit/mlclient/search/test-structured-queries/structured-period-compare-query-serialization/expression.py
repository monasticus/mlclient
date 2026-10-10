"""Test PeriodCompareQuery through its public API."""

from mlclient.search.structured import PeriodCompareQuery


def run():
    return PeriodCompareQuery("system", "aln_equals", "valid", options=["cached"])
