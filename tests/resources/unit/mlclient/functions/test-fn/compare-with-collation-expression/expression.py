from mlclient.functions.xqy import cts, fn


def run():
    return fn.compare(
        "comparand1", "comparand2", collation=fn.string(cts.search().pos(1)),
    ).compile()
