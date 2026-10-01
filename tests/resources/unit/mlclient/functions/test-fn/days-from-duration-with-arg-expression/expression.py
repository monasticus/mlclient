from mlclient.functions.xqy import cts, fn


def run():
    return fn.days_from_duration(fn.string(cts.search().index(1))).compile()
