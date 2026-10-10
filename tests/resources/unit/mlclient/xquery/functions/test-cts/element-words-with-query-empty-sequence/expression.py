from mlclient.xquery import cts


def run():
    return cts.element_words("item", query=None).compile()
