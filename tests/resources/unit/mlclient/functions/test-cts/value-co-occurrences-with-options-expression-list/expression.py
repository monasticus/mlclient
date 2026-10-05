from mlclient.functions.xqy import cts, fn


def run():
    return cts.value_co_occurrences(
        cts.element_reference("price"),
        cts.element_reference("price"),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
