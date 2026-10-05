from mlclient.functions.xqy import cts, fn


def run():
    return fn.function_available(
        "fn:count", arity=fn.count(cts.search().pos(1)),
    ).compile()
