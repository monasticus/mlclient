from mlclient.xquery import cts, fn


def run():
    return cts.range_query(
        cts.element_reference("price"), "=", fn.count(cts.search().pos(1)),
    ).compile()
