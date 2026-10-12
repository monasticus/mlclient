from mlclient.xquery import cts


def run():
    return cts.field_value_query("price", ["1", "2"], options="exact", weight=3)
