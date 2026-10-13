from mlclient.xquery import cts


def run():
    return cts.cluster(None).compile()
