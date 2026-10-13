from mlclient.xquery import cts


def run():
    return cts.collections(forest_ids=None).compile()
