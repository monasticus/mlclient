from mlclient.search.options import QualityWeight, SearchOptions


def run():
    return SearchOptions(QualityWeight(0.5))
