from mlclient.functions.xqy import cts, xs


def run():
    return xs.decimal(
        cts.sum_aggregate(cts.element_reference("price")),
    ).compile()
