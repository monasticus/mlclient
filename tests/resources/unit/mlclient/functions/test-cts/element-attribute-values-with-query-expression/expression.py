from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_values(
        "item", "id", query=cts.collection_query("products"),
    ).compile()
