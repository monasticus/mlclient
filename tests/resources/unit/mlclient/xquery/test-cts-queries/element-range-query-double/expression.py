"""Native ``cts:element-range-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts, xs


def run():
    return cts.element_range_query("price", ">", xs.double(1.5))
