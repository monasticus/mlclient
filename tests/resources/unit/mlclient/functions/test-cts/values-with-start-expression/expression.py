from mlclient.functions.xqy import cts, fn


def run():
    return cts.values(
        cts.element_reference("price"), start=fn.count(cts.search().index(1)),
    ).compile()
