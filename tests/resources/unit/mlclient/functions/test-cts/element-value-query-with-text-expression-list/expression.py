from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_value_query(
        "item", [fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
    ).compile()
