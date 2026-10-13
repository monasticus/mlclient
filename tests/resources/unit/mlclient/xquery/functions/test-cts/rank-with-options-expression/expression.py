from mlclient.xquery import cts, fn


def run():
    return cts.rank("arg", "value", options=fn.string(cts.search().pos(1))).compile()
