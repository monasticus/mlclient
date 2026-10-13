from mlclient.xquery import cts, fn


def run():
    return fn.concat("parameter1", fn.count(cts.search().pos(1))).compile()
