"""Test PeriodRangeQuery through its public API."""

from mlclient.search.structured import Period, PeriodRangeQuery


def run():
    return PeriodRangeQuery(
        ["valid", "system"],
        "aln_contains",
        [Period("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")],
        options=["cached"],
        weight=2,
    )
