from mlclient.xquery import cts


def run():
    return cts.collections(quality_weight=None).compile()
