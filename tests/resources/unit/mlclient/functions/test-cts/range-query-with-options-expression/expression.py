from mlclient.functions.xqy import cts, fn


def run():
    return cts.range_query(
        cts.element_reference("price"),
        "=",
        "value",
        options=fn.string(cts.search().pos(1)),
    ).compile()
