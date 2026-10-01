from mlclient.functions.xqy import cts, fn


def run():
    return cts.match_regions(
        cts.element_reference("price"),
        "operation",
        cts.box(10, 10, 20, 20),
        forest_ids=[fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
