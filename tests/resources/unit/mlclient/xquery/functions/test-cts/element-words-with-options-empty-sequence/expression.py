from mlclient.xquery import cts


def run():
    return cts.element_words("item", options=None).compile()
