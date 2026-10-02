from mlclient.functions.xqy import cts, fn


def run():
    return cts.range_query(
        cts.element_reference("price"), fn.string(cts.search().pos(1)), "value",
    ).compile()
