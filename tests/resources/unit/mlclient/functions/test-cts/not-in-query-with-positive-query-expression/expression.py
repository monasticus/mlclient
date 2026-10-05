from mlclient.functions.xqy import cts


def run():
    return cts.not_in_query(
        cts.collection_query("products"), "negative-query",
    ).compile()
