from mlclient.functions.xqy import cts, fn


def run():
    return fn.escape_uri(fn.string(cts.search().index(1)), True).compile()
