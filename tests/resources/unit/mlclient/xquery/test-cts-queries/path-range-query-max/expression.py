from mlclient.xquery import cts


def run():
    return cts.path_range_query("/item/price", ">", 1, options="cached", weight=3)
