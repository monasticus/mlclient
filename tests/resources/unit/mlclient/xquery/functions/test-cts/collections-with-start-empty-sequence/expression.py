from mlclient.xquery import cts


def run():
    return cts.collections(start=None).compile()
