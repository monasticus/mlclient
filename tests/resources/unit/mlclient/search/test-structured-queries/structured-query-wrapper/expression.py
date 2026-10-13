from mlclient.search.structured import CollectionQuery, Query, TermQuery


def run():
    return Query([TermQuery("blue"), CollectionQuery("reports")])
