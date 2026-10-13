from mlclient.xquery import cts, fn


def run():
    return fn.subsequence(cts.search().pos(1), 2.5, length=object())
