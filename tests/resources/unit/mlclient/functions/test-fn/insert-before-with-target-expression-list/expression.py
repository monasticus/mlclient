from mlclient.functions.xqy import cts, fn


def run():
    return fn.insert_before(
        [cts.search().pos(1), cts.search().pos(2)], 2, cts.search().pos(1),
    ).compile()
