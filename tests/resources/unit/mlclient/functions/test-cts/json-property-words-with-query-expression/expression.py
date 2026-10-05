from mlclient.functions.xqy import cts


def run():
    return cts.json_property_words(
        "price", query=cts.collection_query("products"),
    ).compile()
