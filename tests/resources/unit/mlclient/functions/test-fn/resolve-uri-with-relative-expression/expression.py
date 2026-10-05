from mlclient.functions.xqy import cts, fn


def run():
    return fn.resolve_uri(fn.string(cts.search().pos(1))).compile()
