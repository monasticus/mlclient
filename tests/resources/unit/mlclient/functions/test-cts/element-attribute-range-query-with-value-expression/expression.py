from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_range_query(
        "item", "id", "=", fn.count(cts.search().pos(1)),
    ).compile()
