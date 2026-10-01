from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_word_query("item", set(), "MarkLogic search")
