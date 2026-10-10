from mlclient.xquery import cts, fn


def run():
    return fn.subsequence(
        cts.search().pos(1), fn.count(cts.search().pos(1)),
    ).compile()
