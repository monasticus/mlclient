from mlclient.xquery import cts


def run():
    return cts.aggregate(
        "/ext/aggregate.so",
        "total",
        cts.element_reference("price"),
        options=["checked"],
    ).compile()
