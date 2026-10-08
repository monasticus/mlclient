from mlclient.xquery import cts, fn


def run():
    return cts.element_range_query(
        "item", fn.string(cts.search().pos(1)), "value",
    ).compile()
