from mlclient.search.options import SearchOptions


def run():
    return SearchOptions().control("quality-weight", 0.5)
