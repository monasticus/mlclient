from mlclient.functions.xqy import cts, fn


def run():
    return cts.value_tuples(
        cts.element_reference("price"),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
