from mlclient.xquery import cts


def run():
    return cts.element_word_match("item", "prod*", quality_weight=set())
