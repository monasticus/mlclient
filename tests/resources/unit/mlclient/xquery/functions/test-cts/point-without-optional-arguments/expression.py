from mlclient.xquery import cts


def run():
    return cts.point("POINT (20 10)").compile()
