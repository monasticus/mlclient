from mlclient.functions.xqy import cts, fn


def run():
    return fn.subsequence(cts.search().index(1), 2.5).compile()
