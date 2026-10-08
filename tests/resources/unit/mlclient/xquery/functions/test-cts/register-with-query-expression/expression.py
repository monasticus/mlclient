from mlclient.xquery import cts


def run():
    return cts.register(cts.collection_query("products")).compile()
