from datetime import datetime
from mlclient.functions.xqy import cts, fn


def run():
    return fn.adjust_date_time_to_timezone(
        datetime(2026, 1, 2, 3, 4, 5), timezone=fn.string(cts.search().index(1)),
    ).compile()
