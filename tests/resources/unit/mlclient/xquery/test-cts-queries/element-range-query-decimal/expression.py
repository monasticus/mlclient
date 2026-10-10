"""Native ``cts:element-range-query`` serialization through the public CTS builder."""

from decimal import Decimal
from mlclient.xquery import cts


def run():
    return cts.element_range_query("price", "<", Decimal("1.5"))
