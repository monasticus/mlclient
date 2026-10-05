from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_value_ranges(
        "item",
        "id",
        bounds=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
