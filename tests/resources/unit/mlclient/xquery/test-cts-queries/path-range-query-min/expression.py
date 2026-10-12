"""Native ``cts:path-range-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.path_range_query("/item/price", ">", 1)
