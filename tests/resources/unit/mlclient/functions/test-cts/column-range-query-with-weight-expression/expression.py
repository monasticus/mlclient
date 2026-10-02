from mlclient.functions.xqy import cts, fn


def run():
    return cts.column_range_query(
        "main", "products", "price", "value", weight=fn.count(cts.search().pos(1)),
    ).compile()
