from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_range_query(
        "description",
        "=",
        [fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
