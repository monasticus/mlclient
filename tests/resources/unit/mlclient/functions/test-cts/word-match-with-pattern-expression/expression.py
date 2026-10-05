from mlclient.functions.xqy import cts, fn


def run():
    return cts.word_match(fn.string(cts.search().pos(1))).compile()
