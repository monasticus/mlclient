from mlclient.functions.xqy import cts


def run():
    return cts.linear_model(
        cts.search().index(1), query=cts.collection_query("products"),
    ).compile()
