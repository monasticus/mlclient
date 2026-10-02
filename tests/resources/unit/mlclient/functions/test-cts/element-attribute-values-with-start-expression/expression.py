from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_values(
        "item", "id", start=fn.count(cts.search().pos(1)),
    ).compile()
