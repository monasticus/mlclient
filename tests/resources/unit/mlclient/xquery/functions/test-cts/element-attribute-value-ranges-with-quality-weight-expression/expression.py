from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_value_ranges(
        "item", "id", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
