from mlclient.search.structured import Period, PeriodRangeQuery


def run():
    return PeriodRangeQuery(
        "valid",
        "bogus",
        Period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
    )
