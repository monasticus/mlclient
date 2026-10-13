from mlclient.xquery import cts


def run():
    return cts.parse(cts.collection_query("products")).compile()
