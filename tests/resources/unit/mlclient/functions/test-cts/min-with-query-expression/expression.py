from mlclient.functions.xqy import cts


def run():
    return cts.min(
        cts.element_reference("price"), query=cts.collection_query("products"),
    ).compile()
