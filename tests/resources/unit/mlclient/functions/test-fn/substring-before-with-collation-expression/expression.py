from mlclient.functions.xqy import cts, fn


def run():
    return fn.substring_before(
        "MarkLogic", "needle", collation=fn.string(cts.search().index(1)),
    ).compile()
