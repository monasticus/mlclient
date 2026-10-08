from mlclient.xquery import cts


def run():
    return cts.collection_match(
        "prod*", query=cts.collection_query("products"),
    ).compile()
