from decimal import Decimal
from mlclient.search.structured import RangeQuery
from mlclient.search.structured import JsonProperty


def run():
    return RangeQuery(JsonProperty("price"), Decimal("2.50"))
