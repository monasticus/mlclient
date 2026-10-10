from mlclient.xquery import cts, fn, xs


def run():
    return xs.string(
        fn.count(cts.values(cts.element_reference("price"))),
    ).compile()
