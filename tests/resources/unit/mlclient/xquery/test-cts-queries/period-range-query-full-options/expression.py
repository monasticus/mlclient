"""Native ``cts:period-range-query`` serialization through the public CTS builder."""

import datetime
from mlclient.xquery import cts

START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
END = datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc)


def run():
    return cts.period_range_query(
        ["valid", "system"],
        "aln_before",
        period=cts.period(START, END),
        options="cached",
    )
