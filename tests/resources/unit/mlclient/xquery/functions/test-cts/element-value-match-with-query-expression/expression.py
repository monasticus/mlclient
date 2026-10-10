from mlclient.xquery import cts


def run():
    return cts.element_value_match(
        "item", "prod*", query=cts.collection_query("products"),
    ).compile()
