from mlclient.functions.xqy import cts


def run():
    return cts.correlation(
        cts.element_reference("price"),
        cts.element_reference("price"),
        options="checked",
        query="needle",
        forest_ids=123,
    ).compile()
