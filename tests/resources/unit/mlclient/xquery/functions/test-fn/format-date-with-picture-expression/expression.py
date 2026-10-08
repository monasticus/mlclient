from datetime import date
from mlclient.xquery import cts, fn


def run():
    return fn.format_date(date(2026, 1, 2), fn.string(cts.search().pos(1))).compile()
