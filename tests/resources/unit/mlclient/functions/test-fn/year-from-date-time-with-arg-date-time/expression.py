from datetime import datetime
from mlclient.functions.xqy import fn


def run():
    return fn.year_from_date_time(datetime(2026, 1, 2, 3, 4, 5)).compile()
