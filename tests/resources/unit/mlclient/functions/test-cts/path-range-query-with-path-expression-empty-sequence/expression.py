from mlclient.functions.xqy import cts


def run():
    return cts.path_range_query(None, "=", "value").compile()
