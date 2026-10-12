from mlclient.search.structured import TermQuery


def run():
    return TermQuery("blue", weight=float("-inf"))
