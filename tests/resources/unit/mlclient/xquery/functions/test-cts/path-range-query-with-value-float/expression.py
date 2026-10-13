from mlclient.xquery import cts


def run():
    return cts.path_range_query("/p:item", "=", 2.5).compile()
