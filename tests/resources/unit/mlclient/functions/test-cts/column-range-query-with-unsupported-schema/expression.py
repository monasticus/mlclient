from mlclient.functions.xqy import cts


def run():
    return cts.column_range_query(set(), "products", "price", "value")
