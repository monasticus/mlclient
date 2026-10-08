from datetime import datetime
from mlclient.xquery import fn


def run():
    return fn.subtract_date_times_yielding_day_time_duration(
        fn.current_date_time(), datetime(2026, 1, 2, 3, 4, 5),
    ).compile()
