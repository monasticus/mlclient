from mlclient.xquery import cts


def run():
    return cts.element_word_match(None, "prod*").compile()
