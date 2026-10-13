from mlclient.xquery import cts


def run():
    return cts.estimate(forest_ids=None).compile()
