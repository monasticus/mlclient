from mlclient.functions.xqy import cts


def run():
    return cts.path_range_query("/p:item", "contains", "value")
