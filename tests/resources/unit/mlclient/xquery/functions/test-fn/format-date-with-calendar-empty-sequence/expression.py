from datetime import date
from mlclient.xquery import fn


def run():
    return fn.format_date(
        date(2026, 1, 2), "[Y0001]-[M01]-[D01]", calendar=None,
    ).compile()
