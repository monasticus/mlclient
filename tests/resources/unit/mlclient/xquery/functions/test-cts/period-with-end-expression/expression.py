from datetime import datetime
from mlclient.xquery import cts, fn


def run():
    return cts.period(datetime(2026, 1, 2, 3, 4, 5), fn.current_date_time()).compile()
