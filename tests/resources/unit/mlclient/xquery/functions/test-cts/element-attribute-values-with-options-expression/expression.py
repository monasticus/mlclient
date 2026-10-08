from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_values(
        "item", "id", options=fn.string(cts.search().pos(1)),
    ).compile()
