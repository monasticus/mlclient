from datetime import datetime
from mlclient.functions.xqy import cts, fn


def run():
    return cts.period_compare(
        cts.period(datetime(2026, 1, 1), datetime(2026, 2, 1)),
        fn.string(cts.search().index(1)),
        cts.period(datetime(2026, 1, 1), datetime(2026, 2, 1)),
    ).compile()
