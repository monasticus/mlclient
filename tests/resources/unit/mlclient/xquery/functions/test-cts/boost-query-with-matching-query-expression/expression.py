from mlclient.xquery import cts


def run():
    return cts.boost_query(cts.collection_query("products"), "boosting-query").compile()
