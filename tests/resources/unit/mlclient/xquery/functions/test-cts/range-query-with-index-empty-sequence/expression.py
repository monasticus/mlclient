from mlclient.xquery import cts


def run():
    return cts.range_query(None, "=", "value").compile()
