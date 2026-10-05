from mlclient.functions.xqy import cts


def run():
    return cts.aggregate(
        "/ext/aggregate.so",
        "total",
        cts.element_reference("price"),
        argument=cts.search().pos(1),
    ).compile()
