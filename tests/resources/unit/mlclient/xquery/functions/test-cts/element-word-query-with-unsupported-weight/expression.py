from mlclient.xquery import cts


def run():
    return cts.element_word_query("item", "MarkLogic search", weight=set())
