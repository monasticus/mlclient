from mlclient.functions.xqy import cts, fn


def run():
    return fn.string_join(
        [cts.search().pos(1), cts.search().pos(2)], "parameter2",
    ).compile()
