from mlclient.xquery import cts


def run():
    return cts.rank("arg", "value").compile()
