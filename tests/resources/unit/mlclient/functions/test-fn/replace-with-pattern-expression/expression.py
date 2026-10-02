from mlclient.functions.xqy import cts, fn


def run():
    return fn.replace(
        "MarkLogic", fn.string(cts.search().pos(1)), "database",
    ).compile()
