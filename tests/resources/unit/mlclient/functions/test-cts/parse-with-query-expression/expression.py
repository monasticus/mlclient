from mlclient.functions.xqy import cts


def run():
    return cts.parse(cts.collection_query("products")).compile()
