from datetime import datetime
from mlclient.xquery import fn


def run():
    return fn.subtract_date_times_yielding_year_month_duration(
        object(), datetime(2026, 1, 2, 3, 4, 5),
    )
