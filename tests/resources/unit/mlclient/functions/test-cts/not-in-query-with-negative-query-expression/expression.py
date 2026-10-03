from mlclient.functions.xqy import cts


def run():
    return cts.not_in_query(
        "positive-query", cts.collection_query("products"),
    ).compile()
