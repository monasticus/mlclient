from mlclient.functions.xqy import cts, fn


def run():
    return fn.normalize_unicode(fn.string(cts.search().pos(1))).compile()
