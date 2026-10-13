from mlclient.xquery import cts, fn


def run():
    return cts.count_aggregate(
        cts.element_reference("price"),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
