from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_value_query(
        "item", options=fn.string(cts.search().pos(1)),
    ).compile()
