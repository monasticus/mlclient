"""Native ``cts:element-range-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.element_range_query("price", ">=", 10, options="min-occurs=1", weight=2)
