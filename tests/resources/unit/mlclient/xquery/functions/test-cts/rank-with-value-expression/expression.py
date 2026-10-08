from mlclient.xquery import cts, fn


def run():
    return cts.rank("arg", fn.count(cts.search().pos(1))).compile()
