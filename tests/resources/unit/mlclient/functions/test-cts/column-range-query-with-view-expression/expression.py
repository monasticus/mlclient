from mlclient.functions.xqy import cts, fn


def run():
    return cts.column_range_query(
        "main", fn.string(cts.search().pos(1)), "price", "value",
    ).compile()
