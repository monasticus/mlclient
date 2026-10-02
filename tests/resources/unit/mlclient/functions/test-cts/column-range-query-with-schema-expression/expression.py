from mlclient.functions.xqy import cts, fn


def run():
    return cts.column_range_query(
        fn.string(cts.search().pos(1)), "products", "price", "value",
    ).compile()
