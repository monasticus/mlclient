from datetime import date
from mlclient.functions.xqy import cts, fn


def run():
    return fn.format_date(date(2026, 1, 2), fn.string(cts.search().index(1))).compile()
