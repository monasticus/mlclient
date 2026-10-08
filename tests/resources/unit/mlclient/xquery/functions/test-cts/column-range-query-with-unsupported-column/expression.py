from mlclient.xquery import cts


def run():
    return cts.column_range_query("main", "products", set(), "value")
