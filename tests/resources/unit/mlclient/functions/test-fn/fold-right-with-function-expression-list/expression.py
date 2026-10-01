from mlclient.functions.xqy import cts, fn


def run():
    return fn.fold_right(
        [cts.search().index(1), cts.search().index(2)],
        cts.search().index(1),
        cts.search().index(1),
    ).compile()
