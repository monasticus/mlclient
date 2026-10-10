from mlclient.xquery import cts


def run():
    return cts.column_range_query(
        "main",
        "products",
        "price",
        "value",
        operator="=",
        options="checked",
        weight=2.5,
    ).compile()
