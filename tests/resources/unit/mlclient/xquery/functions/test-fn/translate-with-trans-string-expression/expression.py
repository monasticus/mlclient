from mlclient.xquery import cts, fn


def run():
    return fn.translate("src", "abc", fn.string(cts.search().pos(1))).compile()
