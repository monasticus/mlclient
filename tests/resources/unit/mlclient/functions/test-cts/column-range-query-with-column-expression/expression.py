from mlclient.functions.xqy import cts, fn


def run():
    return cts.column_range_query(
        "main", "products", fn.string(cts.search().index(1)), "value",
    ).compile()
