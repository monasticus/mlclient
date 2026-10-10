from mlclient.xquery import cts, fn


def run():
    return cts.values(
        cts.element_reference("price"), quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
