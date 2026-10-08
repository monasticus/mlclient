from datetime import date
from mlclient.xquery import xs


def run():
    return xs.date(date(2026, 1, 2)).compile()
