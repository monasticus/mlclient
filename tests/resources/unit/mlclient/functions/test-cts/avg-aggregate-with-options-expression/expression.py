from mlclient.functions.xqy import cts, fn


def run():
    return cts.avg_aggregate(
        cts.element_reference("price"), options=fn.string(cts.search().index(1)),
    ).compile()
