from datetime import datetime
from mlclient.functions.xqy import fn


def run():
    return fn.format_date_time(
        datetime(2026, 1, 2, 3, 4, 5),
        "[Y0001]-[M01]-[D01]T[H01]:[m01]:[s01]",
        country=object(),
    )
