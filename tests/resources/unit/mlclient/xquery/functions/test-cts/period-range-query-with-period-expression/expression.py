from datetime import datetime
from mlclient.xquery import cts


def run():
    return cts.period_range_query(
        "valid",
        "aln_before",
        period=cts.period(datetime(2026, 1, 1), datetime(2026, 2, 1)),
    ).compile()
