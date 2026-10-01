from mlclient.functions.xqy import cts, fn


def run():
    return fn.hours_from_duration(fn.string(cts.search().index(1))).compile()
