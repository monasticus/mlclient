from datetime import date
from mlclient.functions.xqy import cts, fn


def run():
    return fn.adjust_date_to_timezone(
        date(2026, 1, 2), timezone=fn.string(cts.search().pos(1)),
    ).compile()
