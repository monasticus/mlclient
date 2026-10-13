from mlclient.xquery import cts


def run():
    return cts.query(cts.collection_query("products")).compile()
