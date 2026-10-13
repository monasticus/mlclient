from mlclient.xquery import cts, fn


def run():
    return cts.field_values(fn.string(cts.search().pos(1))).compile()
