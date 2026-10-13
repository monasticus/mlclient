from mlclient.xquery import cts


def run():
    return cts.circle(2.5, cts.point(10, 20)).compile()
