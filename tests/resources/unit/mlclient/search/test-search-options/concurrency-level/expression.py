from mlclient.search.options import ConcurrencyLevel, SearchOptions


def run():
    return SearchOptions(ConcurrencyLevel(4))
