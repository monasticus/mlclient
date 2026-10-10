from mlclient.xquery import cts


def run():
    return cts.match_regions(set(), "operation", cts.box(10, 10, 20, 20))
