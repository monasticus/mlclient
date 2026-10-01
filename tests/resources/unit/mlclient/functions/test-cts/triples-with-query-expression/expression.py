from mlclient.functions.xqy import cts


def run():
    return cts.triples(query=cts.collection_query("products")).compile()
