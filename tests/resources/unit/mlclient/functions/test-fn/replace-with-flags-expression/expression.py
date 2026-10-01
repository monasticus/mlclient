from mlclient.functions.xqy import cts, fn


def run():
    return fn.replace(
        "MarkLogic", "logic", "database", flags=fn.string(cts.search().index(1)),
    ).compile()
