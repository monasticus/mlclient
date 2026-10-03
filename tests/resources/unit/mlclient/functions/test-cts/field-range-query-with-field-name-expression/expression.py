from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_range_query(
        fn.string(cts.search().pos(1)), "=", "value",
    ).compile()
