from mlclient.xquery import cts


def run():
    return cts.point(10.0, 2.5).compile()
