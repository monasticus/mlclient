from mlclient.search.structured import TermQuery


def run():
    return TermQuery("a < b & c")
