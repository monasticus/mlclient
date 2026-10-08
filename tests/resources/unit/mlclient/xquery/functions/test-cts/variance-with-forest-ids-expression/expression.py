from mlclient.xquery import cts, fn


def run():
    return cts.variance(
        cts.element_reference("price"), forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
