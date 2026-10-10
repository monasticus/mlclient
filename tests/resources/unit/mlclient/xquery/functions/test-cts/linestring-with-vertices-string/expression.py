from mlclient.xquery import cts


def run():
    return cts.linestring("LINESTRING (10 10, 20 20)").compile()
