from mlclient.functions.xqy import cts


def run():
    return cts.words(query=cts.collection_query("products")).compile()
