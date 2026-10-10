from mlclient.xquery import cts, fn


def run():
    return fn.fold_left(
        [cts.search().pos(1), cts.search().pos(2)],
        cts.search().pos(1),
        cts.search().pos(1),
    ).compile()
