from decimal import Decimal

from mlclient.search.structured import JsonProperty, RangeQuery


def run():
    return RangeQuery(JsonProperty("price"), Decimal("2.50"))
