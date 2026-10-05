from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_co_occurrences(
        "item", "item", query=cts.collection_query("products"),
    ).compile()
