from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_value_match(
        "item", "id", fn.count(cts.search().pos(1)),
    ).compile()
