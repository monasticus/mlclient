from mlclient.functions.xqy import fn


def run():
    return fn.unparsed_text("document.txt", encoding="UTF-8").compile()
