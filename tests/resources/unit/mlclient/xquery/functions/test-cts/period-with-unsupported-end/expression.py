from datetime import datetime
from mlclient.xquery import cts


def run():
    return cts.period(datetime(2026, 1, 2, 3, 4, 5), set())
