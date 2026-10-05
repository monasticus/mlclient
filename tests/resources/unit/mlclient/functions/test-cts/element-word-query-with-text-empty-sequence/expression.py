from mlclient.functions.xqy import cts


def run():
    return cts.element_word_query("item", None).compile()
