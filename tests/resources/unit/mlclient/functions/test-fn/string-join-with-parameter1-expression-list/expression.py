from mlclient.functions.xqy import cts, fn


def run():
    return fn.string_join(
        [cts.search().index(1), cts.search().index(2)], "parameter2",
    ).compile()
