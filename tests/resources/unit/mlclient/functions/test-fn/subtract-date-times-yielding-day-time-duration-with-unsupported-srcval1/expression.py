from datetime import datetime
from mlclient.functions.xqy import fn


def run():
    return fn.subtract_date_times_yielding_day_time_duration(
        object(), datetime(2026, 1, 2, 3, 4, 5),
    )
