from mlclient.functions.xqy import cts


def run():
    return cts.percent_rank("arg", True).compile()
