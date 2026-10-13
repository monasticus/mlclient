from mlclient.xquery import cts, fn


def run():
    return cts.aggregate(
        "/ext/aggregate.so",
        fn.string(cts.search().pos(1)),
        cts.element_reference("price"),
    ).compile()
