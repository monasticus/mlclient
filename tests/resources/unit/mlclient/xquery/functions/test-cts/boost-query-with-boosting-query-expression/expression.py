from mlclient.xquery import cts


def run():
    return cts.boost_query("matching-query", cts.collection_query("products")).compile()
