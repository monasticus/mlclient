from datetime import date
from mlclient.xquery import fn


def run():
    return fn.year_from_date(date(2026, 1, 2)).compile()
