from datetime import date
from mlclient.xquery import fn


def run():
    return fn.date_time(date(2026, 1, 2), fn.current_time()).compile()
