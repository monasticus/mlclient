from mlclient.xquery import cts, fn


def run():
    return cts.element_range_query(
        "item",
        "=",
        "value",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
