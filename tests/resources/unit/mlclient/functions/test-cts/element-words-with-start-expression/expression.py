from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_words("item", start=fn.string(cts.search().pos(1))).compile()
