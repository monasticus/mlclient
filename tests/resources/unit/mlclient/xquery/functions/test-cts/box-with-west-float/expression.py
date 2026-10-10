from mlclient.xquery import cts


def run():
    return cts.box(2.5, 2.5, 2.5, 2.5).compile()
