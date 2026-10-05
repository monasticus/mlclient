from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_word_query("item", None, "MarkLogic search").compile()
