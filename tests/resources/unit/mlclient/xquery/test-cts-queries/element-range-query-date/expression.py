"""Native ``cts:element-range-query`` serialization through the public CTS builder."""

import datetime
from mlclient.xquery import cts


def run():
    return cts.element_range_query("day", ">", datetime.date(2026, 1, 1))
