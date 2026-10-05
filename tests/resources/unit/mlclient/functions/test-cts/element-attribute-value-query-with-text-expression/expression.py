from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_value_query(
        "item", "id", fn.string(cts.search().pos(1)),
    ).compile()
