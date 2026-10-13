from mlclient.xquery import cts


def run():
    return cts.element_word_query(None, "MarkLogic search").compile()
