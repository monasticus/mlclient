from mlclient.functions.xqy import cts, fn, xs


def run():
    return xs.string(
        fn.count(cts.values(cts.element_reference("price"))),
    ).compile()
