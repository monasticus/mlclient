from mlclient.xquery import cts, fn


def run():
    return fn.codepoints_to_string(fn.count(cts.search().pos(1))).compile()
