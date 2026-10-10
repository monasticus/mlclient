from datetime import datetime
from mlclient.xquery import fn


def run():
    return fn.adjust_date_time_to_timezone(
        datetime(2026, 1, 2, 3, 4, 5), timezone=object(),
    )
