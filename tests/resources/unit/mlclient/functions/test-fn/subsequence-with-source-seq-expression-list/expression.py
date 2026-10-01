from mlclient.functions.xqy import cts, fn


def run():
    return fn.subsequence([cts.search().index(1), cts.search().index(2)], 2.5).compile()
