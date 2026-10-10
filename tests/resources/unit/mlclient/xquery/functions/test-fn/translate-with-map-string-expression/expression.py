from mlclient.xquery import cts, fn


def run():
    return fn.translate("src", fn.string(cts.search().pos(1)), "ABC").compile()
