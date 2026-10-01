from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_range_query(
        "item", "id", fn.string(cts.search().index(1)), "value",
    ).compile()
