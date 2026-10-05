from mlclient.functions.xqy import cts, fn


def run():
    return fn.tokenize(
        "MarkLogic", "logic", flags=fn.string(cts.search().pos(1)),
    ).compile()
