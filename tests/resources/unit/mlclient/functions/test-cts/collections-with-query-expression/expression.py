from mlclient.functions.xqy import cts


def run():
    return cts.collections(query=cts.collection_query("products")).compile()
