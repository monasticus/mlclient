from datetime import date, time
from mlclient.xquery import fn


def run():
    return fn.date_time(date(2026, 1, 2), time(3, 4, 5)).compile()
