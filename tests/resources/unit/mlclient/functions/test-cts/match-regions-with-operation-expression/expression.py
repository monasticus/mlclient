from mlclient.functions.xqy import cts, fn


def run():
    return cts.match_regions(
        cts.element_reference("price"),
        fn.string(cts.search().index(1)),
        cts.box(10, 10, 20, 20),
    ).compile()
