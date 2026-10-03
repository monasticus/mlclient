from mlclient.functions.xqy import cts


def run():
    return cts.element_words("item", start=None).compile()
