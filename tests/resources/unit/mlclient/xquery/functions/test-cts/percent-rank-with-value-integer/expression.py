from mlclient.xquery import cts


def run():
    return cts.percent_rank("arg", 123).compile()
