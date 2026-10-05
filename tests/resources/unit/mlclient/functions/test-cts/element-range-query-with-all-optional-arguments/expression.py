from mlclient.functions.xqy import cts


def run():
    return cts.element_range_query(
        "item", "=", "value", options="checked", weight=2.5,
    ).compile()
