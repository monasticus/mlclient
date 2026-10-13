from mlclient.xquery import cts


def run():
    return cts.column_range_query(set(), "products", "price", "value")
