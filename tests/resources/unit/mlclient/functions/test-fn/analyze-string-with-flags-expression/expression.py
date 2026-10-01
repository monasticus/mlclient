from mlclient.functions.xqy import cts, fn


def run():
    return fn.analyze_string(
        "MarkLogic", "logic", flags=fn.string(cts.search().index(1)),
    ).compile()
