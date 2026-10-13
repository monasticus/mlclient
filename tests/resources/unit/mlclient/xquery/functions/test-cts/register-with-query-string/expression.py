from mlclient.xquery import cts


def run():
    return cts.register("needle").compile()
