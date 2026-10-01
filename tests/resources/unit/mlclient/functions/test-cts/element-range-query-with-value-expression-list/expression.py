from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_range_query(
        "item", "=", [fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
