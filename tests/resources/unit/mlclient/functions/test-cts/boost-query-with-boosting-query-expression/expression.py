from mlclient.functions.xqy import cts


def run():
    return cts.boost_query("matching-query", cts.collection_query("products")).compile()
