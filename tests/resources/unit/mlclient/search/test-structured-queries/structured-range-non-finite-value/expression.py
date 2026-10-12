from decimal import Decimal

from mlclient.search.structured import Element, RangeQuery


def run():
    return RangeQuery(Element("price"), Decimal("NaN"), operator="LT")
