from mlclient.xquery import cts


def run():
    return cts.uris(query=cts.collection_query("products")).compile()
