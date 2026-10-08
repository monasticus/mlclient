from mlclient.xquery import cts


def run():
    return cts.deregister(123).compile()
