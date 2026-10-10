from mlclient.xquery import cts, fn


def run():
    return cts.percent_rank("arg", fn.count(cts.search().pos(1))).compile()
