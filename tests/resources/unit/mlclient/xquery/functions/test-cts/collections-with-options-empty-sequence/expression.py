from mlclient.xquery import cts


def run():
    return cts.collections(options=None).compile()
