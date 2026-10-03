from mlclient.functions.xqy import cts


def run():
    return cts.query(cts.collection_query("products")).compile()
