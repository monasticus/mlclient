from mlclient.xquery import cts


def run():
    return cts.value_match(
        cts.element_reference("price"), "prod*", query=cts.collection_query("products"),
    ).compile()
