from mlclient.xquery import cts


def run():
    return cts.estimate(cts.collection_query("products")).compile()
