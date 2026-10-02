from mlclient.functions.xqy import cts, fn


def run():
    return fn.insert_before(cts.search().pos(1), 2, None).compile()
