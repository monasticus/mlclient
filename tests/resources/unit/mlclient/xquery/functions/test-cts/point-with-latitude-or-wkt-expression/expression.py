from mlclient.xquery import cts, fn


def run():
    return cts.point(fn.string("POINT (20 10)")).compile()
