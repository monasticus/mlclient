from mlclient.xquery import cts, fn


def run():
    return fn.regex_group(fn.count(cts.search().pos(1))).compile()
