from mlclient.xquery import cts


def run():
    return cts.collections(query=cts.collection_query("products")).compile()
