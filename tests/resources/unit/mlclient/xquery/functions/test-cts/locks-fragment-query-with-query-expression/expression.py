from mlclient.xquery import cts


def run():
    return cts.locks_fragment_query(cts.collection_query("products")).compile()
