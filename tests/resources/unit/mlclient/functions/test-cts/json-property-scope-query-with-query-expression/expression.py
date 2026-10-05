from mlclient.functions.xqy import cts


def run():
    return cts.json_property_scope_query(
        "price", cts.collection_query("products"),
    ).compile()
