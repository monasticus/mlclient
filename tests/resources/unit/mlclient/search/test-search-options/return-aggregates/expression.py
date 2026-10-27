from mlclient.search.options import ReturnAggregates, SearchOptions


def run():
    return SearchOptions(ReturnAggregates(False))
