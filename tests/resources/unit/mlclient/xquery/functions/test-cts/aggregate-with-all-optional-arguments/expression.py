from mlclient.xquery import cts


def run():
    return cts.aggregate(
        "/ext/aggregate.so",
        "total",
        cts.element_reference("price"),
        argument=cts.search().pos(1),
        options="checked",
        query="needle",
        forest_ids=123,
    ).compile()
