from mlclient.functions.xqy import cts, fn


def run():
    return cts.min(
        cts.element_reference("price"), options=fn.string(cts.search().pos(1)),
    ).compile()
