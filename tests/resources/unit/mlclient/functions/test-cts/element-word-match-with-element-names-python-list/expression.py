from mlclient.functions.xqy import cts


def run():
    return cts.element_word_match(["item"], "prod*").compile()
