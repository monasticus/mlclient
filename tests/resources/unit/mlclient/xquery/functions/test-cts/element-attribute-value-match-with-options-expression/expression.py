from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_value_match(
        "item", "id", "prod*", options=fn.string(cts.search().pos(1)),
    ).compile()
