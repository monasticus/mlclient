from mlclient.xquery import cts


def run():
    return cts.polygon("POLYGON ((10 10, 20 10, 20 20, 10 10))").compile()
