from mlclient.search.options import ReturnSimilar, SearchOptions


def run():
    return SearchOptions(ReturnSimilar(True))
