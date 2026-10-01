from mlclient.functions.xqy import cts


def run():
    return cts.aggregate(
        "/ext/aggregate.so",
        "total",
        cts.element_reference("price"),
        argument=[cts.search().index(1), cts.search().index(2)],
    ).compile()
