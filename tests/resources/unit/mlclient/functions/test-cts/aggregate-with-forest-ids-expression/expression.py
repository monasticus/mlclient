from mlclient.functions.xqy import cts, fn


def run():
    return cts.aggregate(
        "/ext/aggregate.so",
        "total",
        cts.element_reference("price"),
        forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
