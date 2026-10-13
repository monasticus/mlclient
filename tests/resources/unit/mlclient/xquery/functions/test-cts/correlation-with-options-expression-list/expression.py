from mlclient.xquery import cts, fn


def run():
    return cts.correlation(
        cts.element_reference("price"),
        cts.element_reference("price"),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
