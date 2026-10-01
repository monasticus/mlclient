from mlclient.functions.xqy import cts


def run():
    return cts.field_range_query(None, "=", "value").compile()
