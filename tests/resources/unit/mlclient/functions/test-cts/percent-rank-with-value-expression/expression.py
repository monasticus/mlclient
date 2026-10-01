from mlclient.functions.xqy import cts, fn


def run():
    return cts.percent_rank("arg", fn.count(cts.search().index(1))).compile()
