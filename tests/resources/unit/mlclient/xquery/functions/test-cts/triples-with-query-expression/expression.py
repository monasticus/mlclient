from mlclient.xquery import cts


def run():
    return cts.triples(query=cts.collection_query("products")).compile()
