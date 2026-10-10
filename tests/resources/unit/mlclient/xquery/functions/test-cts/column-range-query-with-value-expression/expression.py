from mlclient.xquery import cts, fn


def run():
    return cts.column_range_query(
        "main", "products", "price", fn.count(cts.search().pos(1)),
    ).compile()
