from mlclient.search.structured import NearQuery, TermQuery


def run():
    return NearQuery(TermQuery("blue"), distance=0, distance_weight=0)
