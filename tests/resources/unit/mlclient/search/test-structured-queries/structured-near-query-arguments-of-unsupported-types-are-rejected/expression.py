from mlclient.search.structured import NearQuery, TermQuery


def run():
    return NearQuery([TermQuery("a")], distance=1.5)
