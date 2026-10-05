from mlclient.functions.xqy import cts


def run():
    return cts.path_range_query("/p:item", "=", ["value", 123, 2.5, True]).compile()
