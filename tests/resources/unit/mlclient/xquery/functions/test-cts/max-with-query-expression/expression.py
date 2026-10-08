from mlclient.xquery import cts


def run():
    return cts.max(
        cts.element_reference("price"), query=cts.collection_query("products"),
    ).compile()
