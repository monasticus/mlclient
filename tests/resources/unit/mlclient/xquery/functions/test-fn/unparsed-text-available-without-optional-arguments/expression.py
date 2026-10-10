from mlclient.xquery import fn


def run():
    return fn.unparsed_text_available("document.txt").compile()
