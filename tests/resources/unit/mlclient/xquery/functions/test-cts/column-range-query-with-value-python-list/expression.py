from mlclient.xquery import cts


def run():
    return cts.column_range_query(
        "main", "products", "price", ["value", 123, 2.5, True],
    ).compile()
