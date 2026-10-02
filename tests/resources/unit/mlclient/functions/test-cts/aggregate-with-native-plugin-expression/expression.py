from mlclient.functions.xqy import cts, fn


def run():
    return cts.aggregate(
        fn.string(cts.search().pos(1)), "total", cts.element_reference("price"),
    ).compile()
