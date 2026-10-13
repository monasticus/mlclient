from mlclient.xquery import cts


def run():
    return cts.collections(query=None).compile()
