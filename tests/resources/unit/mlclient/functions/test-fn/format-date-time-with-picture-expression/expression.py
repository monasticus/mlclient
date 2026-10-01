from datetime import datetime
from mlclient.functions.xqy import cts, fn


def run():
    return fn.format_date_time(
        datetime(2026, 1, 2, 3, 4, 5), fn.string(cts.search().index(1)),
    ).compile()
