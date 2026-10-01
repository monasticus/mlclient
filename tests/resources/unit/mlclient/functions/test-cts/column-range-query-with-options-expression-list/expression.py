from mlclient.functions.xqy import cts, fn


def run():
    return cts.column_range_query(
        "main",
        "products",
        "price",
        "value",
        options=[fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
    ).compile()
