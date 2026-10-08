from datetime import datetime
from mlclient.xquery import cts, fn


def run():
    return cts.period_compare(
        cts.period(datetime(2026, 1, 1), datetime(2026, 2, 1)),
        fn.string(cts.search().pos(1)),
        cts.period(datetime(2026, 1, 1), datetime(2026, 2, 1)),
    ).compile()
