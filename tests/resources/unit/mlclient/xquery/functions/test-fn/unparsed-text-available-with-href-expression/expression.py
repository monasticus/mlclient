from mlclient.xquery import cts, fn


def run():
    return fn.unparsed_text_available(fn.string(cts.search().pos(1))).compile()
