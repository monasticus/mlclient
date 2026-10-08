from mlclient.xquery import cts, fn


def run():
    return fn.escape_uri(fn.string(cts.search().pos(1)), True).compile()
