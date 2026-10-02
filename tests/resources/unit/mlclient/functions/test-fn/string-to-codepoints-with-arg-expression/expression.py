from mlclient.functions.xqy import cts, fn


def run():
    return fn.string_to_codepoints(fn.string(cts.search().pos(1))).compile()
