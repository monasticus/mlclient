from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_value_ranges(
        "item",
        "id",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
