from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_range_query(
        "item", "id", "=", "value", weight=fn.count(cts.search().pos(1)),
    ).compile()
