from mlclient.functions.xqy import cts, fn


def run():
    return cts.value_co_occurrences(
        cts.element_reference("price"),
        cts.element_reference("price"),
        quality_weight=fn.count(cts.search().index(1)),
    ).compile()
