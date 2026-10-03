from mlclient.functions.xqy import cts


def run():
    return cts.column_range_query("main", set(), "price", "value")
