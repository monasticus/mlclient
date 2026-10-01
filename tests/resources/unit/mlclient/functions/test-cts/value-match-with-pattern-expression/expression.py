from mlclient.functions.xqy import cts, fn


def run():
    return cts.value_match(
        cts.element_reference("price"), fn.count(cts.search().index(1)),
    ).compile()
