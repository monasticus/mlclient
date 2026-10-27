from mlclient.search import options as o


def run():
    return o.SearchOptions(o.SortOrder("quality-order", direction="descending"))
