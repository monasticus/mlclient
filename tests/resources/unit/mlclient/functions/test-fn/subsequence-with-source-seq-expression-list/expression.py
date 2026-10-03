from mlclient.functions.xqy import cts, fn


def run():
    return fn.subsequence([cts.search().pos(1), cts.search().pos(2)], 2.5).compile()
