from datetime import datetime, timezone
from mlclient.xquery import xs


def run():
    return xs.date_time(
        datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
    ).compile()
