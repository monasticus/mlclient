"""Native ``cts:field-range-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.field_range_query("price", "<=", 2)
