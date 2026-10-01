from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_words("item", options=fn.string(cts.search().index(1))).compile()
