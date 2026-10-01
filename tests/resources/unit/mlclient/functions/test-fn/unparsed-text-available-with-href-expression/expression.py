from mlclient.functions.xqy import cts, fn


def run():
    return fn.unparsed_text_available(fn.string(cts.search().index(1))).compile()
