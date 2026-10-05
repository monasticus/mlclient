from mlclient.functions.xqy import cts, fn


def run():
    return fn.doc(fn.string(cts.search().pos(1))).compile()
