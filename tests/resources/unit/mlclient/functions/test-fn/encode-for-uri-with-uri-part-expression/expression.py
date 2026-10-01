from mlclient.functions.xqy import cts, fn


def run():
    return fn.encode_for_uri(fn.string(cts.search().index(1))).compile()
