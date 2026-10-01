from mlclient.functions.xqy import cts, fn


def run():
    return cts.column_range_query(
        fn.string(cts.search().index(1)), "products", "price", "value",
    ).compile()
