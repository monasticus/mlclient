from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_range_query(
        "item", "id", fn.string(cts.search().pos(1)), "value",
    ).compile()
