from mlclient.xquery import cts


def run():
    return cts.element_attribute_words(
        "item", "id", query=cts.collection_query("products"),
    ).compile()
