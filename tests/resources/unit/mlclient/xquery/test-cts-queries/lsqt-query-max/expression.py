"""Native ``cts:lsqt-query`` serialization through the public CTS builder."""

import datetime
from mlclient.xquery import cts

START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def run():
    return cts.lsqt_query("temporal", timestamp=START, options="cached", weight=2)
