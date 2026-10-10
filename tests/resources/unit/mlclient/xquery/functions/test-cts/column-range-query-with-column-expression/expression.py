from mlclient.xquery import cts, fn


def run():
    return cts.column_range_query(
        "main", "products", fn.string(cts.search().pos(1)), "value",
    ).compile()
