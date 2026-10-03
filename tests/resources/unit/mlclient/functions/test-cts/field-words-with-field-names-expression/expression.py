from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_words(fn.string(cts.search().pos(1))).compile()
