from mlclient.xquery import cts, fn


def run():
    return fn.contains(
        "parameter1", "parameter2", collation=fn.string(cts.search().pos(1)),
    ).compile()
