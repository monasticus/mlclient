from mlclient.search.structured import PathIndex, RangeQuery


def run():
    return RangeQuery(PathIndex("/report/price"), 2, operator="LT")
