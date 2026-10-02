from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_range_query(
        "item", "=", "value", weight=fn.count(cts.search().pos(1)),
    ).compile()
