from mlclient.xquery import cts


def run():
    return cts.rank("arg", 2.5).compile()
