from mlclient.functions.xqy import cts, fn


def run():
    return fn.analyze_string(fn.string(cts.search().index(1)), "logic").compile()
