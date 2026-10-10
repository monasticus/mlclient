from mlclient.xquery import cts, fn


def run():
    return fn.max("arg", collation=fn.string(cts.search().pos(1))).compile()
