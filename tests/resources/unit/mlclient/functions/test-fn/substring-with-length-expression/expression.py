from mlclient.functions.xqy import cts, fn


def run():
    return fn.substring(
        "source-string", 2.5, length=fn.count(cts.search().pos(1)),
    ).compile()
