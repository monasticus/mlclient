from mlclient.xquery import cts, fn


def run():
    return fn.format_number(2.5, fn.string(cts.search().pos(1))).compile()
