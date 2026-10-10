from mlclient.xquery import cts, fn


def run():
    return fn.analyze_string(
        "MarkLogic", "logic", flags=fn.string(cts.search().pos(1)),
    ).compile()
