from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_range_query(
        "item", fn.string(cts.search().index(1)), "value",
    ).compile()
