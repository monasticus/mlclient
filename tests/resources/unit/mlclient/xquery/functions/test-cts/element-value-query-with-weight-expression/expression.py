from mlclient.xquery import cts, fn


def run():
    return cts.element_value_query(
        "item", weight=fn.count(cts.search().pos(1)),
    ).compile()
