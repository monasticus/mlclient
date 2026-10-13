from mlclient.xquery import cts


def run():
    return cts.element_range_query("item", "=", ["value", 123, 2.5, True]).compile()
