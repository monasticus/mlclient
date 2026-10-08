from datetime import datetime
from mlclient.xquery import cts, fn


def run():
    return cts.period(fn.current_date_time(), datetime(2026, 1, 2, 3, 4, 5)).compile()
