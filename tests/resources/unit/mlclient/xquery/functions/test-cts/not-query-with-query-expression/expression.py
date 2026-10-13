from mlclient.xquery import cts


def run():
    return cts.not_query(cts.collection_query("products")).compile()
