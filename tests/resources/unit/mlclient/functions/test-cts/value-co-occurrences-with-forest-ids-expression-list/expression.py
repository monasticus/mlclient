from mlclient.functions.xqy import cts, fn


def run():
    return cts.value_co_occurrences(
        cts.element_reference("price"),
        cts.element_reference("price"),
        forest_ids=[fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
