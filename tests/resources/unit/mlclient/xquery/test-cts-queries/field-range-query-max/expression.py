from mlclient.xquery import cts


def run():
    return cts.field_range_query("price", "<=", 2, options="cached", weight=3)
