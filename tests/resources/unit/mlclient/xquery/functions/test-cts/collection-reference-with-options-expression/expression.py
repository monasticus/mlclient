from mlclient.xquery import cts, fn


def run():
    return cts.collection_reference(options=fn.string(cts.search().pos(1))).compile()
