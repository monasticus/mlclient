from mlclient.xquery import cts


def run():
    return cts.search(cts.collection_query("products")).compile()
