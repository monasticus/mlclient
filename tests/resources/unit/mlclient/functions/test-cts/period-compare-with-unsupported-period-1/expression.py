from datetime import datetime
from mlclient.functions.xqy import cts


def run():
    return cts.period_compare(
        set(), "aln_before", cts.period(datetime(2026, 1, 1), datetime(2026, 2, 1)),
    )
