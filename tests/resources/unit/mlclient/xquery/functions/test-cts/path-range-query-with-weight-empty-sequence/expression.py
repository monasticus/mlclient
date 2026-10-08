from mlclient.xquery import cts


def run():
    return cts.path_range_query("/p:item", "=", "value", weight=None).compile()
