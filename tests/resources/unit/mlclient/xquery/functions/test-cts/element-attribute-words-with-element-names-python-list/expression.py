from mlclient.xquery import cts


def run():
    return cts.element_attribute_words(["item"], "id").compile()
