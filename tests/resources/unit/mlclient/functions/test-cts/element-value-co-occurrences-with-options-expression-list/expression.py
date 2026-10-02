from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_value_co_occurrences(
        "item",
        "item",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
