from mlclient.xquery import cts, fn


def run():
    return cts.value_ranges(
        cts.element_reference("price"), options=fn.string(cts.search().pos(1)),
    ).compile()
