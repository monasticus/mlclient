from datetime import date
from mlclient.xquery import fn


def run():
    return fn.adjust_date_to_timezone(date(2026, 1, 2), timezone=None).compile()
