from mlclient.search.structured import PathIndex
from mlclient.search.structured import RangeQuery


def run():
    return RangeQuery(PathIndex("/report/price"), 2, operator="LT")
