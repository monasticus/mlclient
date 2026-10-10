from mlclient.xquery import cts


def run():
    return cts.words(query=cts.collection_query("products")).compile()
