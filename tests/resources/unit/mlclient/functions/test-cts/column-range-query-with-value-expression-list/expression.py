from mlclient.functions.xqy import cts, fn


def run():
    return cts.column_range_query(
        "main",
        "products",
        "price",
        [fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
