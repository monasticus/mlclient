from mlclient.search.structured import TermQuery
from mlclient.search.structured import NearQuery


def run():
    return NearQuery(TermQuery("blue"), distance=0, distance_weight=0)
