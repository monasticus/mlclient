from datetime import datetime
from mlclient.functions.xqy import cts


def run():
    return cts.period(set(), datetime(2026, 1, 2, 3, 4, 5))
