"""Native ``cts:element-range-query`` serialization through the public CTS builder."""

import datetime
from mlclient.xquery import cts

START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def run():
    return cts.element_range_query("at", "<=", START)
