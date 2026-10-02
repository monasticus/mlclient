from mlclient.functions.xqy import cts, fn


def run():
    return cts.value_ranges(
        cts.element_reference("price"), quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
