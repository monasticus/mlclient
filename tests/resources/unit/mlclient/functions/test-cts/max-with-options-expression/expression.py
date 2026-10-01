from mlclient.functions.xqy import cts, fn


def run():
    return cts.max(
        cts.element_reference("price"), options=fn.string(cts.search().index(1)),
    ).compile()
