from mlclient.functions.xqy import cts, fn


def run():
    return fn.contains(
        "parameter1", "parameter2", collation=fn.string(cts.search().index(1)),
    ).compile()
