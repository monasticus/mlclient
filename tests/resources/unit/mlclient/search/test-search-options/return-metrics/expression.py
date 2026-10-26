from mlclient.search.options import ReturnMetrics, SearchOptions


def run():
    return SearchOptions(ReturnMetrics(False))
