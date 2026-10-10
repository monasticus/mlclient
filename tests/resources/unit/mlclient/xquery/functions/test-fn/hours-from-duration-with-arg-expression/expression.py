from mlclient.xquery import cts, fn


def run():
    return fn.hours_from_duration(fn.string(cts.search().pos(1))).compile()
