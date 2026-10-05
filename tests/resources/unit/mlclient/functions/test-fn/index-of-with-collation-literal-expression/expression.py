from mlclient.functions.xqy import cts, fn


def run():
    return fn.index_of(
        "seq-param", "srch-param", collation_literal=fn.string(cts.search().pos(1)),
    ).compile()
