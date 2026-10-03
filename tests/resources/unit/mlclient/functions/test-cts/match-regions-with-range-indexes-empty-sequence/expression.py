from mlclient.functions.xqy import cts


def run():
    return cts.match_regions(None, "operation", cts.box(10, 10, 20, 20)).compile()
