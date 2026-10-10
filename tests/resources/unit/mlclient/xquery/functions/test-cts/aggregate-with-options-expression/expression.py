from mlclient.xquery import cts, fn


def run():
    return cts.aggregate(
        "/ext/aggregate.so",
        "total",
        cts.element_reference("price"),
        options=fn.string(cts.search().pos(1)),
    ).compile()
