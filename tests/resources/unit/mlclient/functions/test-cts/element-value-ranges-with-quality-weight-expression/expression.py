from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_value_ranges(
        "item", quality_weight=fn.count(cts.search().index(1)),
    ).compile()
