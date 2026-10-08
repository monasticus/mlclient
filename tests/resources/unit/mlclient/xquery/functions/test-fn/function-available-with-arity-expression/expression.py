from mlclient.xquery import cts, fn


def run():
    return fn.function_available(
        "fn:count", arity=fn.count(cts.search().pos(1)),
    ).compile()
