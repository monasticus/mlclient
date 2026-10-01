from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_value_co_occurrences(
        "item", "id", "item", "id", quality_weight=fn.count(cts.search().index(1)),
    ).compile()
