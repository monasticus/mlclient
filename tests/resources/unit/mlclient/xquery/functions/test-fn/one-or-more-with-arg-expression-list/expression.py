from mlclient.xquery import cts, fn


def run():
    return fn.one_or_more([cts.search().pos(1), cts.search().pos(2)]).compile()
