from mlclient.functions.xqy import cts, fn


def run():
    return fn.subsequence(cts.search().pos(1), 2.5, length=None).compile()
