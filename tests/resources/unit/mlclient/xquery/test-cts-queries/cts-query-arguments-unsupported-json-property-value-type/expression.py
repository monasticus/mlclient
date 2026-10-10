"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import datetime
from mlclient.xquery import cts


def run():
    query = cts.json_property_value_query("day", datetime.date(2026, 1, 1))
    return query.serialize()
