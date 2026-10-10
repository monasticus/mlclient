from mlclient.xquery import cts, fn


def run():
    return cts.element_value_ranges(
        "item", forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
